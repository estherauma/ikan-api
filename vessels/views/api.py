from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from vessels.models import Vessel, VesselImage
from vessels.serializers import VesselSerializer, VesselImageSerializer
from contracts.models import ContractClause
import json
from django.db.models import Q


class VesselApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselSerializer
    queryset = Vessel.objects.all()

    def list(self, request):
        request.data.pop('id', None)
        user = self.request.user
        super_user = user.is_superuser
        groups = user.groups.all()

        if super_user:
            vessels = self.get_queryset()
        elif 'worker' in [group.name for group in groups]:  # check caters for users with multiple roles
            user_contract_clauses = ContractClause.objects.filter(contract__contract_user_access__user=user)
            party_b_clauses = user_contract_clauses.filter(kind='contract-clauses-parties-requirement-fishers')
            party_b_data = party_b_clauses.values('content')
            vessel_app_refs = [json.loads(item['content'])['vessel'] for item in party_b_data]
            vessels = Vessel.objects.filter(
                Q(app_ref__in=vessel_app_refs) |
                Q(created_by=request.user.id)  # for users with multiple roles
            )
        else:
            vessels = Vessel.objects.filter(created_by=request.user.id)

        serializer = self.get_serializer(vessels, many=True)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data,
            },
            status.HTTP_200_OK
        )

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class VesselApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselSerializer
    queryset = Vessel.objects.all()

    def get_vessel(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return Vessel.objects.get(id=id)
            else:
                return Vessel.objects.get(id=id, created_by=req.user.id)
        except Vessel.DoesNotExist:
            raise ValidationError('Vessel does not exist')

    def retrieve(self, request, id):
        vessel = self.get_vessel(req=request, id=id)
        serializer = self.serializer_class(vessel)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        vessel = self.get_vessel(req=request, id=id)
        serializer = self.serializer_class(vessel, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        vessel = self.get_vessel(req=request, id=id)
        user_id = request.user.id

        if user_id != vessel.created_by:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        vessel.delete()
        return Response({
            'status': 'OK',
            'data': id
        }, status.HTTP_200_OK)


class VesselImageApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselImageSerializer
    queryset = VesselImage.objects.all()

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class VesselImageApiDetailListView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselImageSerializer
    queryset = VesselImage.objects.all()

    def get_vessel_image(self, req, id):
        try:

            super_user = self.request.user.is_superuser
            if super_user:
                return VesselImage.objects.get(id=id)
            else:
                return VesselImage.objects.get(id=id, created_by=req.user.id)
        except VesselImage.DoesNotExist:
            raise ValidationError('Vessel image does not exist')

    def retrieve(self, request, id):
        vessel_image = self.get_vessel_image(req=request, id=id)
        serializer = self.serializer_class(vessel_image)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        vessel_image = self.get_vessel_image(req=request, id=id)
        serializer = self.serializer_class(vessel_image, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        vessel_image = self.get_vessel_image(req=request, id=id)
        user_id = request.user.id

        if user_id != vessel_image.created_by:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        vessel_image.delete()
        return Response({
            'status': 'OK',
            'data': id
        }, status.HTTP_200_OK)
