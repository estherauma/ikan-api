from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from wages.models import Wage
from wages.serializers import WageSerializer


class WageApiListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WageSerializer

    def get_queryset(self):
        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        if is_super_user:
            return Wage.objects.all()
        elif "worker" in roles:
            return Wage.objects.filter(user=user)
        elif "vessel_owner" in roles:
            return Wage.objects.filter(created_by=user.id)
        else:
            return Wage.objects.none()
