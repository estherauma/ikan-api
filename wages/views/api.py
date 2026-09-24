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
from django.utils.dateparse import parse_datetime
from django.db.models import Q


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
        req_user = self.request.user

        if req_user.is_superuser:
            qs = Wage.objects.all()
        else:
            qs = Wage.objects.filter(
                Q(user=req_user) |
                Q(created_by=req_user.id) |
                Q(user__recruited_by=req_user)
            ).distinct()
        try:
            return qs.get(id=id)
        except Wage.DoesNotExist:
            raise ValidationError({'error': 'Wage payment does not exist or access denied'})

    def retrieve(self, request, id):
        wage = self.get_wage(id)
        serializer = self.serializer_class(wage)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        wage = self.get_wage(id)
        if req_updated_at is None or req_updated_at > wage.updated_at:
            serializer = self.serializer_class(
                wage, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user.id)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.'
            }, status=status.HTTP_200_OK)
