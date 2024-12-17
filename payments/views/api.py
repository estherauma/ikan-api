from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentApiListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        if is_super_user:
            return Payment.objects.all()
        elif "worker" in roles:
            return Payment.objects.filter(user=user)
        elif "vessel_owner" in roles:
            return Payment.objects.filter(created_by=user.id)
        else:
            return Payment.objects.none()
