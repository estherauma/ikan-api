def get_user_queryset():
    """
    Returns a queryset of all users with related groups, banks, and beneficiaries prefetched.
    This helps to optimize database queries and reduce the number of queries executed when accessing related objects.
    """
    from accounts.models import User

    return User.objects.prefetch_related('groups', 'userbank_set', 'userbeneficiaries_set').all()
