from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        has_required_role = any(group.name in self.required_roles for group in request.user.groups.all())
        if not request.user.is_superuser and not has_required_role:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
