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
from django.utils.dateparse import parse_datetime
from vessels.utils import get_vessel_queryset


class VesselApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselSerializer
    queryset = get_vessel_queryset()

    def get_worker_vessels(self, user):
        user_contract_clauses = ContractClause.objects.filter(contract__contract_user_access__user=user)
        party_b_clauses = user_contract_clauses.filter(kind='contract-clauses-parties-requirement-fishers')
        party_b_data = party_b_clauses.values('content')
        vessel_app_refs = []
        for item in party_b_data:
            try:
                vessel_ref = json.loads(item['content']).get('vessel')
                if vessel_ref:
                    vessel_app_refs.append(vessel_ref)
            except (KeyError, json.JSONDecodeError):
                continue

        return get_vessel_queryset().filter(
                Q(app_ref__in=vessel_app_refs) |
                Q(created_by=user.id)  # for users with multiple roles
            )

    def list(self, request):
        request.data.pop('id', None)
        user = self.request.user
        super_user = user.is_superuser
        is_worker = any(group.name == 'worker' for group in user.groups.all())

        if super_user:
            vessels = get_vessel_queryset()
        elif is_worker:
            vessels = self.get_worker_vessels(user)
        else:
            vessels = get_vessel_queryset().filter(created_by=request.user.id)

        serializer = self.get_serializer(vessels, many=True)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data
            },
            status.HTTP_200_OK
        )

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class VesselApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = VesselSerializer
    queryset = get_vessel_queryset()

    def get_vessel(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return get_vessel_queryset().get(id=id)
            else:
                return get_vessel_queryset().get(id=id, created_by=req.user.id)
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
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        vessel = self.get_vessel(req=request, id=id)
        if req_updated_at is None or req_updated_at > vessel.updated_at:
            serializer = self.serializer_class(vessel, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(vessel).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        vessel = self.get_vessel(req=request, id=id)
        user_id = request.user.id

        if user_id != vessel.created_by_id:
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
        serializer.save(created_by=request.user)
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
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        vessel_image = self.get_vessel_image(req=request, id=id)
        if req_updated_at is None or req_updated_at > vessel_image.updated_at:
            serializer = self.serializer_class(vessel_image, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(vessel_image).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        vessel_image = self.get_vessel_image(req=request, id=id)
        user_id = request.user.id

        if user_id != vessel_image.created_by_id:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        vessel_image.delete()
        return Response({
            'status': 'OK',
            'data': id
        }, status.HTTP_200_OK)
