# rest_framework imports
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
# Model imports
from contracts.models import Contract, ContractClause, ContractDocument

# Serializer imports
from contracts.serializers import (
    ContractSerializer, contractClauseSerializer, ContractDocumentSerializer
)

from django.utils.dateparse import parse_datetime


class ContractListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContractSerializer

    def get_queryset(self):
        """
        Return the queryset based on whether the user is a superuser or not.
        """
        user = self.request.user
        if user.is_superuser:
            return Contract.objects.all()

        # Filter contracts created by the user or where the user has access
        return Contract.objects.filter(
            Q(created_by=user.id) |
            Q(contract_user_access__user=user.id)
        ).distinct()

    def list(self, request, *args, **kwargs):
        """
        Override the list method to return a custom response format.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request):
        # remove the id field from request.data so ids from the local
        # db aren't used
        # alternatively, update the serializer to ignore the id field on input
        # extra_kwargs = {
        # 'id': {'read_only': True}
        # }
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def get_item(self, id):
        req_user = self.request.user
        if req_user.is_superuser:
            qs = Contract.objects.all()
        else:
            qs = Contract.objects.filter(
                Q(created_by=req_user.id) |
                Q(contract_user_access__user=req_user.id)
            ).distinct()

        try:
            return qs.get(id=id)
        except Contract.DoesNotExist:
            raise ValidationError({'error': 'Contract not found OR access denied.'})

    def retrieve(self, request, id):
        contract = self.get_item(id)
        serializer = self.serializer_class(contract)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract = self.get_item(id)
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > contract.updated_at:
            serializer = self.serializer_class(contract, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(contract).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        # TODO: Implement more granular permission checks for deleting contracts.
        # Currently, only admin users are allowed to delete contracts.
        if not request.user.is_admin:
            raise ValidationError({'error': 'Access denied.'})

        contract = self.get_item(id)
        contract.delete()
        return Response({
            'status': 'OK',
            'message': 'Contract deleted successfully'
        }, status=status.HTTP_200_OK)


class ContractClauseListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = contractClauseSerializer

    def get_queryset(self):
        """
        Return the list of contract clauses based on the user's contract access.
        """
        user = self.request.user

        if user.is_superuser:
            return ContractClause.objects.all()

        return ContractClause.objects.filter(
            Q(contract__created_by=user.id) |
            Q(contract__contract_user_access__user=user.id)
        ).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractClauseDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = contractClauseSerializer
    queryset = ContractClause.objects.all()

    def get_item(self, id):
        req_user = self.request.user
        if req_user.is_superuser:
            qs = ContractClause.objects.all()
        else:
            qs = ContractClause.objects.filter(
                Q(contract__created_by=req_user.id) |
                Q(contract__contract_user_access__user=req_user.id)
            ).distinct()

        try:
            return qs.get(id=id)
        except ContractClause.DoesNotExist:
            raise ValidationError({'error': 'Contract clause does not exist or access denied.'})

    def retrieve(self, request, id):
        contract_clause = self.get_item(id)
        serializer = self.serializer_class(contract_clause)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract_clause = self.get_item(id)
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > contract_clause.updated_at:
            serializer = self.serializer_class(contract_clause, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(contract_clause).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        # TODO: Implement more granular permission checks for deleting contract clauses.
        # Currently, only admin users are allowed to delete contract clauses.
        if not request.user.is_admin:
            raise ValidationError({'error': 'Access denied.'})

        contract_clause = self.get_item(id)
        contract_clause.delete()
        return Response({
            'status': 'OK',
            'message': 'Contract clause deleted successfully'
        }, status=status.HTTP_200_OK)


class ContractDocumentListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractDocumentSerializer
    queryset = ContractDocument.objects.all()

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDocumentDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractDocumentSerializer
    queryset = ContractDocument.objects.all()

    def get_item(self, id):
        req_user = self.request.user
        if req_user.is_superuser:
            qs = ContractDocument.objects.all()
        else:
            qs = ContractDocument.objects.filter(
                Q(contract__created_by=req_user.id) |
                Q(contract__contract_user_access__user=req_user.id)
            ).distinct()

        try:
            return qs.get(id=id)
        except ContractDocument.DoesNotExist:
            raise ValidationError(
                {'error': 'Contract document does not exist'}
            )

    def retrieve(self, request, id):
        contract_document = self.get_item(id)
        serializer = self.serializer_class(contract_document)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract_document = self.get_item(id)
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > contract_document.updated_at:
            serializer = self.serializer_class(contract_document, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(contract_document).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        # TODO: Implement more granular permission checks for deleting contract documents.
        # Currently, only admin users are allowed to delete contract documents.
        if not request.user.is_admin:
            raise ValidationError({'error': 'Access denied.'})

        contract_document = self.get_item(id)
        contract_document.delete()
        return Response({
            'status': 'OK',
            'message': 'Contract document deleted successfully'
        }, status=status.HTTP_200_OK)
