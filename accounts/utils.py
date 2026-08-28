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
