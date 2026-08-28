import json

from django.db.models import Q

from accounts.models import User
from accounts.serializers import UserProfileSerializer
from companies.models import Company
from companies.serializers import CompanySerializer
from contracts.models import Contract, ContractClause, ContractDocument
from contracts.serializers import (
    ContractSerializer,
    contractClauseSerializer,
    ContractDocumentSerializer,
)
from mydocuments.models import Document, Passport
from mydocuments.serializers import DocumentSerializer, PassportSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from survey.models import InlineQuestion, LearningHubProgress
from survey.serializers import (
    InLineQuestionSerializer,
    LearningHubProgressSerializer,
)
from vessels.models import Vessel
from vessels.serializers import VesselSerializer
from wages.models import Wage
from wages.serializers import WageSerializer
from accounts.utils import get_user_queryset

AGENT_ROLES = ("taiwanese_agent", "indonesian_agent")


def _get_managed_workers(user):
    user_groups = user.groups.values_list("name", flat=True)

    if "vessel_owner" in user_groups:
        return get_user_queryset().filter(created_by=user)
    elif any(role in AGENT_ROLES for role in user_groups):
        return get_user_queryset().filter(recruited_by=user)
    else:
        return User.objects.none()


def _get_worker_vessels(user):
    """Vessels that a worker is attached to, derived from the party B clause on their contracts."""
    party_b_clauses = ContractClause.objects.filter(
        contract__contract_user_access__user=user,
        kind="contract-clauses-parties-requirement-fishers",
    )
    vessel_app_refs = []
    for content in party_b_clauses.values_list("content", flat=True):
        try:
            parsed_content = (
                json.loads(content) if isinstance(content, str) else (content or {})
            )
            vessel_ref = parsed_content.get("vessel")
            if vessel_ref:
                vessel_app_refs.append(vessel_ref)
        except (AttributeError, json.JSONDecodeError):
            continue

    return Vessel.objects.prefetch_related('vessel_image').filter(
        Q(app_ref__in=vessel_app_refs) | Q(created_by=user.id))


def _get_contract_data(contracts):
    """Serialize a contract queryset along with its related clauses and documents."""
    return {
        "contracts": ContractSerializer(contracts, many=True).data,
        "contract_clauses": contractClauseSerializer(
            ContractClause.objects.filter(contract__in=contracts).distinct(), many=True
        ).data,
        "contract_documents": ContractDocumentSerializer(
            ContractDocument.objects.filter(contract__in=contracts).distinct(),
            many=True,
        ).data,
    }


def _get_own_data(user):
    """Data every user owns and can always sync, regardless of role."""
    return {
        # "survey_responses": SurveySerializer(
        #     Survey.objects.filter(user=user), many=True
        # ).data,
        "inline_questions": InLineQuestionSerializer(
            InlineQuestion.objects.filter(user=user), many=True
        ).data,
        "documents": DocumentSerializer(
            Document.objects.filter(user=user), many=True
        ).data,
        "passports": PassportSerializer(
            Passport.objects.filter(user=user), many=True
        ).data,
        "learning_hub_progress": LearningHubProgressSerializer(
            LearningHubProgress.objects.filter(user=user), many=True
        ).data,
        "notifications": NotificationSerializer(
            Notification.objects.filter(user=user), many=True
        ).data,
    }


def _get_worker_sync_data(user):
    contracts = Contract.objects.filter(contract_user_access__user=user).distinct()

    data = {
        "profile": UserProfileSerializer(user).data,
        "vessels": VesselSerializer(_get_worker_vessels(user), many=True).data,
        "wages": WageSerializer(Wage.objects.filter(user=user), many=True).data,
    }
    data.update(_get_contract_data(contracts))
    data.update(_get_own_data(user))
    return data


def _get_vessel_owner_sync_data(user):
    workers_added_by_vo = _get_managed_workers(user)
    agents = user.agents
    users = get_user_queryset().filter(pk=user.id) | workers_added_by_vo
    if agents is not None:
        users = users | agents

    contracts = Contract.objects.filter(
        Q(created_by=user.id) | Q(contract_user_access__user__in=workers_added_by_vo)
    ).distinct()

    data = {
        "profile": UserProfileSerializer(user).data,
        "companies": CompanySerializer(
            Company.objects.filter(created_by=user.id), many=True
        ).data,
        "vessels": VesselSerializer(
            Vessel.objects.filter(created_by=user.id), many=True
        ).data,
        "users": UserProfileSerializer(users.distinct(), many=True).data,
        "wages": WageSerializer(
            Wage.objects.filter(user__in=workers_added_by_vo), many=True
        ).data,
    }
    data.update(_get_contract_data(contracts))
    data.update(_get_own_data(user))
    return data


def _get_agent_sync_data(user):
    workers_recruited_by_agent = _get_managed_workers(user)
    vessel_owners = user.vessel_owners
    users = get_user_queryset().filter(pk=user.id) | workers_recruited_by_agent
    if vessel_owners is not None:
        users = users | vessel_owners

    contracts = Contract.objects.filter(
        Q(created_by=user.id) | Q(contract_user_access__user__in=workers_recruited_by_agent)
    ).distinct()

    data = {
        "profile": UserProfileSerializer(user).data,
        "users": UserProfileSerializer(users.distinct(), many=True).data,
        "wages": WageSerializer(
            Wage.objects.filter(user__in=workers_recruited_by_agent), many=True
        ).data,
    }
    data.update(_get_contract_data(contracts))
    data.update(_get_own_data(user))
    return data


def _get_default_sync_data(user):
    """Fallback for roles without a dedicated sync scope (e.g. public, buyer) - own data only."""
    data = {
        "profile": UserProfileSerializer(user).data,
        "wages": WageSerializer(Wage.objects.filter(user=user), many=True).data,
    }
    data.update(_get_contract_data(Contract.objects.filter(created_by=user.id)))
    data.update(_get_own_data(user))
    return data


def _get_admin_sync_data(user):
    """Superusers can access everything."""
    data = {
        "profile": UserProfileSerializer(user).data,
        "users": UserProfileSerializer(
            get_user_queryset().all(), many=True).data,
        "companies": CompanySerializer(Company.objects.all(), many=True).data,
        "vessels": VesselSerializer(Vessel.objects.all(), many=True).data,
        "wages": WageSerializer(Wage.objects.all(), many=True).data,
    }
    data.update(_get_contract_data(Contract.objects.all()))
    data.update(_get_own_data(user))
    return data


def get_sync_data(user):
    """
    Returns a role-scoped dictionary of data for the given user, used to sync
    the mobile app on login and on-demand sync.
    """
    roles = set(user.groups.values_list("name", flat=True))

    if user.is_superuser:
        return _get_admin_sync_data(user)
    if "worker" in roles:
        return _get_worker_sync_data(user)
    if "vessel_owner" in roles:
        return _get_vessel_owner_sync_data(user)
    if roles.intersection(AGENT_ROLES):
        return _get_agent_sync_data(user)

    return _get_default_sync_data(user)
