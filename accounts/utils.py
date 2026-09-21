import secrets
from datetime import timedelta
from urllib.parse import urlencode

from decouple import config
from django.utils import timezone

from common.email import TunaEmailHelper, EmailTemplate


def get_user_queryset():
    """
    Returns a queryset of all users with related groups, banks, and beneficiaries prefetched.
    This helps to optimize database queries and reduce the number of queries executed when accessing related objects.
    """
    from accounts.models import User

    return User.objects.prefetch_related('groups', 'userbank_set', 'userbeneficiaries_set').all()


def get_workers(request):
    from accounts.models import User

    super_user = request.user.is_superuser
    user_groups = request.user.groups.values_list("name", flat=True)
    is_agent = any(role in user_groups for role in ['indonesian_agent', 'taiwanese_agent'])

    if super_user:
        return get_user_queryset().filter(groups__name='worker')
    elif is_agent:
        return get_user_queryset().filter(groups__name='worker', recruited_by=request.user)
    elif "vessel_owner" in user_groups:
        return get_user_queryset().filter(groups__name='worker', created_by=request.user.id)
    else:
        return User.objects.none()


def send_user_invite_email(user, auth_common_text=None):
    auth_common_text = auth_common_text or {}
    user.reset_password_token = secrets.token_urlsafe(32)
    user.reset_password_token_created_at = timezone.now()
    user.access_code = None
    user.save()

    email_helper = TunaEmailHelper()
    link_query_string = urlencode({
        'email': user.email,
        'token': user.reset_password_token,
    })
    dashboard_link = f'{config("BASE_URL")}/account/setup-account?{link_query_string}'
    return email_helper.tuna_send_email(
        to_emails=[user.email],
        subject=auth_common_text.get('userInviteSubject', 'Set up your IKAN account'),
        body={
            'first_name': user.first_name,
            'dashboard_link': dashboard_link,
        },
        template=EmailTemplate.USER_INVITE.value,
        auth_common_text=auth_common_text,
    )


def is_user_invite_token_valid(user):
    if not user or not user.reset_password_token_created_at:
        return False

    expires_at = user.reset_password_token_created_at + timedelta(days=3)
    return timezone.now() <= expires_at
