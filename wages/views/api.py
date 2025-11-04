from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.permissions import IsAuthenticated
from wages.models import Wage
from wages.serializers import WageSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status


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


class WageApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WageSerializer
    queryset = Wage.objects.all()

    def get_wage(self, id):
        try:
            return Wage.objects.get(id=id)
        except Wage.DoesNotExist:
            raise ValidationError({'error': 'Wage payment does not exist'})

    def retrieve(self, request, id):
        wage = self.get_wage(id)
        serializer = self.serializer_class(wage)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        wage = self.get_wage(id)
        serializer = self.serializer_class(
            wage, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_202_ACCEPTED)
