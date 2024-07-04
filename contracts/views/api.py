# rest_framework imports
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Model imports
from contracts.models import Contract, ContractClause, ContractDocument

# Serializer imports
from contracts.serializers import ContractSerializer, contractClauseSerializer, ContractDocumentSerializer


class ContractListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def list(self, request):
        super_user = self.request.user.is_superuser
        queryset = self.get_queryset() if super_user else Contract.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'OK', 'data': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request):
        # remove the id field from request.data so ids from the local db aren't used
        # alternatively, update the serializer to ignore the id field on input
        # extra_kwargs = {
        # 'id': {'read_only': True}
        # }
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def get_item(self, id):
        try:
            return Contract.objects.get(id=id)
        except Contract.DoesNotExist:
            raise ValidationError({'error': 'Contract does not exist'})

    def retrieve(self, request, id):
        contract = self.get_item(id)
        serializer = self.serializer_class(contract)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract = self.get_item(id)
        serializer = self.serializer_class(contract, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        pass


class ContractClauseListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = contractClauseSerializer
    queryset = ContractClause.objects.all()

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractClauseDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = contractClauseSerializer
    queryset = ContractClause.objects.all()

    def get_item(self, id):
        try:
            return ContractClause.objects.get(id=id)
        except ContractClause.DoesNotExist:
            raise ValidationError({'error': 'Contract clause does not exist'})

    def retrieve(self, request, id):
        contract_clause = self.get_item(id)
        serializer = self.serializer_class(contract_clause)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract_clause = self.get_item(id)
        serializer = self.serializer_class(contract_clause, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        pass


class ContractDocumentListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractDocumentSerializer
    queryset = ContractDocument.objects.all()

    def create(self, request):
        request.data.pop('id', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDocumentDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = ContractDocumentSerializer
    queryset = ContractDocument.objects.all()

    def get_item(self, id):
        try:
            return ContractDocument.objects.get(id=id)
        except ContractDocument.DoesNotExist:
            raise ValidationError({'error': 'Contract document does not exist'})

    def retrieve(self, request, id):
        contract_document = self.get_item(id)
        serializer = self.serializer_class(contract_document)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        contract_document = self.get_item(id)
        serializer = self.serializer_class(contract_document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        pass
