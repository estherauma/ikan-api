from accounts.models import User


def get_workers(request):
    super_user = request.user.is_superuser
    roles = request.user.groups.all().values_list("name", flat=True)
    # is_vessel_owner = 'vessel_owner' in roles
    is_agent = any(role in roles for role in ['indonesian_agent', 'taiwanese_agent'])

    users = User.objects.filter(created_by=request.user.id)
    if super_user:
        users = User.objects.all()
    elif is_agent:
        users = User.objects.filter(recruited_by=request.user)

    workers = users.filter(groups__name='worker', created_by=request.user.id)
    if is_agent:
        workers = users.filter(groups__name='worker', recruited_by=request.user)

    return workers
