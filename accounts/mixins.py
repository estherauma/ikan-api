from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        has_required_role = request.user.groups.filter(name__in=self.required_roles).exists()
        if not request.user.is_superuser and not has_required_role:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
