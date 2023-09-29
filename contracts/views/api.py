# rest_framework imports
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Model imports
from contracts.models import Contract, ContractClause

# Serializer imports
from contracts.serializers import ContractSerializer, contractClauseSerializer


class ContractListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated,])
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'statis': 'OK', 'data': serializer.data}, status=status.HTTP_200_OK)
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated,])
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

    def destroy(self, request, id ):
        pass 


class ContractClauseListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated,])
    serializer_class = contractClauseSerializer
    queryset = ContractClause.objects.all()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractClauseDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated,])
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

    def destroy(self, request, id ):
        pass
