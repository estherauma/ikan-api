import json

from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User, UserBank, UserBeneficiaries
from accounts.serializers import (
    UserProfileSerializer,
    UserBankDetailsSerializer,
    UserBeneficiarySerializer,
)
from common.logger import logger
from companies.models import Company
from companies.serializers import CompanySerializer
from survey.models import Survey
from survey.serializers import SurveySerializer
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
OWNER_ROLES = ("vessel_owner",) + AGENT_ROLES
# List-style records owned by the pushing user, matched by online_ref/app_ref.
# learning_hub_progress is handled separately since the payload sends a single object, not a list.
OWNED_SYNC_MODELS = {
    "survey_responses": (Survey, SurveySerializer),
    "inline_questions": (InlineQuestion, InLineQuestionSerializer),
    "documents": (Document, DocumentSerializer),
    "passports": (Passport, PassportSerializer),
    "notifications": (Notification, NotificationSerializer),
}


def _get_managed_workers(user):
    user_groups = user.groups.values_list("name", flat=True)

    if "vessel_owner" in user_groups:
        return get_user_queryset().filter(created_by=user.id)
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


def _match_existing(queryset, record):
    """Find a record the client is updating: use the known server id (online_ref), fall back to app_ref."""
    online_ref = record.get("online_ref")
    if online_ref:
        instance = queryset.filter(pk=online_ref).first()
        if instance:
            return instance
    app_ref = record.get("app_ref")
    if app_ref:
        return queryset.filter(app_ref=app_ref).first()
    return None


def _upsert_record(serializer_class, queryset, record, extra_fields=None):
    """
    Create or update a single record against `queryset` (already scoped to who/what it may belong to),
    ignoring stale offline writes (incoming updated_at <= stored updated_at).
    """
    instance = _match_existing(queryset, record)
    data = {k: v for k, v in record.items() if k not in ("id", "online_ref")}
    if extra_fields:
        data.update(extra_fields)

    incoming_updated_at = parse_datetime(data["updated_at"]) if data.get("updated_at") else None
    if instance and incoming_updated_at and instance.updated_at and incoming_updated_at <= instance.updated_at:
        return instance, serializer_class(instance).data

    serializer = serializer_class(instance, data=data, partial=bool(instance))
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return instance, serializer.data


def _upsert_owned_record(model, serializer_class, owner, record):
    """Create or update a single record owned by `owner`."""
    _, data = _upsert_record(
        serializer_class, model.objects.filter(user=owner), record, extra_fields={"user": owner.id}
    )
    return data


def _upsert_created_by_record(model, serializer_class, user, record):
    """Create or update a single record `user` (VO/agent) owns via created_by, e.g. companies/vessels."""
    _, data = _upsert_record(
        serializer_class, model.objects.filter(created_by=user.id), record, extra_fields={"created_by": user.id}
    )
    return data


def _ensure_owner_role(user, label):
    """Only vessel owners/agents (or superusers) may push companies, vessels or contracts."""
    roles = set(user.groups.values_list("name", flat=True))
    if not (user.is_superuser or roles.intersection(OWNER_ROLES)):
        raise PermissionDenied(f"You do not have permission to sync {label}.")


def _get_syncable_user(user, target_user_id):
    """A profile push may target the pushing user themself, or a worker they manage (VO/agent)."""
    if str(target_user_id) == str(user.id):
        return user
    managed_worker = _get_managed_workers(user).filter(pk=target_user_id).first()
    if managed_worker is None:
        raise PermissionDenied("You do not have permission to sync this profile.")
    return managed_worker


def _upsert_profile(user, record, errors):
    """Update a user's own profile, or (for VO/agent) a managed worker's profile, plus its bank/beneficiaries."""
    online_ref = record.get("online_ref") or record.get("id")
    if not online_ref:
        raise ValidationError("Profile sync requires 'online_ref' (the existing user's id).")
    target_user = _get_syncable_user(user, online_ref)

    bank_accounts = record.get("bank_accounts") or []
    beneficiaries = record.get("beneficiaries") or []
    profile_fields = {
        k: v for k, v in record.items() if k not in ("id", "online_ref", "bank_accounts", "beneficiaries")
    }

    serializer = UserProfileSerializer(target_user, data=profile_fields, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    data = serializer.data

    bank_results, bank_errors = [], []
    for bank_record in bank_accounts:
        try:
            bank_results.append(_upsert_owned_record(UserBank, UserBankDetailsSerializer, target_user, bank_record))
        except Exception as exc:
            logger.exception("Sync push failed for bank_accounts (online_ref=%s)", online_ref)
            bank_errors.append(_error_entry(bank_record, exc))
    if bank_errors:
        errors.setdefault("bank_accounts", []).extend(
            {**entry, "profile": online_ref} for entry in bank_errors
        )

    beneficiary_results, beneficiary_errors = [], []
    for beneficiary_record in beneficiaries:
        try:
            beneficiary_results.append(
                _upsert_owned_record(UserBeneficiaries, UserBeneficiarySerializer, target_user, beneficiary_record)
            )
        except Exception as exc:
            logger.exception("Sync push failed for beneficiaries (online_ref=%s)", online_ref)
            beneficiary_errors.append(_error_entry(beneficiary_record, exc))
    if beneficiary_errors:
        errors.setdefault("beneficiaries", []).extend(
            {**entry, "profile": online_ref} for entry in beneficiary_errors
        )

    data["bank_accounts"] = bank_results
    data["beneficiaries"] = beneficiary_results
    return data


def _upsert_contract_with_clauses(user, record, errors):
    """Upsert a contract owned by `user`, then its nested clauses scoped to that contract only."""
    clauses = record.pop("clauses", None) or []
    instance, data = _upsert_record(
        ContractSerializer, Contract.objects.filter(created_by=user.id), record, extra_fields={"created_by": user.id}
    )

    # Clauses are matched within this contract only, never globally - a client can't hijack another
    # contract's clause by guessing its app_ref/online_ref.
    clause_queryset = ContractClause.objects.filter(contract=instance)
    clause_results, clause_errors = [], []
    for clause_record in clauses:
        try:
            _, clause_data = _upsert_record(
                contractClauseSerializer, clause_queryset, clause_record, extra_fields={"contract": instance.id}
            )
            clause_results.append(clause_data)
        except Exception as exc:
            logger.exception("Sync push failed for contract_clauses (contract app_ref=%s)", record.get("app_ref"))
            clause_errors.append(_error_entry(clause_record, exc))
    if clause_errors:
        errors.setdefault("contract_clauses", []).extend(
            {**entry, "contract": record.get("app_ref")} for entry in clause_errors
        )

    data["clauses"] = clause_results
    return data


def _upsert_wage(user, record):
    """Create or update a wage record, restricted to workers `user` (VO/agent) manages."""
    managed_worker_ids = set(_get_managed_workers(user).values_list("id", flat=True))
    if record.get("user") not in managed_worker_ids:
        raise PermissionDenied("You do not have permission to add wages for this user.")

    # Wages have no app_ref, so are matched by raw "id" (online_ref).
    record = {**record, "online_ref": record.get("online_ref", record.get("id"))}
    _, data = _upsert_record(WageSerializer, Wage.objects.filter(user_id__in=managed_worker_ids), record)
    return data


def _error_entry(record, exc):
    """Build a loggable/returnable error entry for a single failed sync record."""
    return {"app_ref": record.get("app_ref"), "online_ref": record.get("online_ref"), "error": str(exc)}


def _sync_section(key, items, upsert_fn, results, errors):
    """Run `upsert_fn` over each item in `items`, collecting successes/failures without aborting the rest."""
    if not items:
        return

    successes, item_errors = [], []
    for record in items:
        try:
            successes.append(upsert_fn(record))
        except Exception as exc:
            logger.exception("Sync push failed for %s (app_ref=%s)", key, record.get("app_ref"))
            item_errors.append(_error_entry(record, exc))

    if successes:
        results[key] = successes
    if item_errors:
        errors[key] = item_errors


def sync_push_data(user, payload):
    """
    Upserts records the mobile app created/updated while offline, scoped to
    what the user's role is permitted to write. Unknown keys are ignored.
    Failed items are logged and reported per-section instead of aborting the whole push.
    """
    results = {}
    errors = {}

    for key, (model, serializer_class) in OWNED_SYNC_MODELS.items():
        _sync_section(
            key, payload.get(key), lambda record, m=model, s=serializer_class: _upsert_owned_record(m, s, user, record),
            results, errors,
        )

    learning_hub_progress = payload.get("learning_hub_progress")
    if learning_hub_progress:
        try:
            results["learning_hub_progress"] = _upsert_owned_record(
                LearningHubProgress, LearningHubProgressSerializer, user, learning_hub_progress
            )
        except Exception as exc:
            logger.exception("Sync push failed for learning_hub_progress")
            errors["learning_hub_progress"] = [_error_entry(learning_hub_progress, exc)]

    # Wage permission checks intentionally bubble up (not caught here) - unauthorized wage pushes
    # must hard-fail the request, unlike the other sections which log-and-continue per item.
    wages = payload.get("wages")
    if wages:
        results["wages"] = [_upsert_wage(user, record) for record in wages]

    if payload.get("companies"):
        _ensure_owner_role(user, "companies")
        _sync_section(
            "companies", payload["companies"],
            lambda record: _upsert_created_by_record(Company, CompanySerializer, user, record), results, errors,
        )

    if payload.get("vessels"):
        _ensure_owner_role(user, "vessels")
        _sync_section(
            "vessels", payload["vessels"],
            lambda record: _upsert_created_by_record(Vessel, VesselSerializer, user, record), results, errors,
        )

    if payload.get("contracts"):
        _ensure_owner_role(user, "contracts")
        _sync_section(
            "contracts", payload["contracts"],
            lambda record: _upsert_contract_with_clauses(user, record, errors), results, errors,
        )

    _sync_section(
        "profiles", payload.get("profiles"), lambda record: _upsert_profile(user, record, errors), results, errors
    )

    survey_records = payload.get("survey_responses")
    survey_synced = bool(survey_records) and bool(results.get("survey_responses")) and "survey_responses" not in errors

    return {
        "pushed_data": results,
        "survey_synced": survey_synced,
        "errors": errors,
    }
