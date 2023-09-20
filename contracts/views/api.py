from requests import Response

# rest_framework imports
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# Model imports
from contracts.models import Contract

# Serializer imports
from contracts.serializers import ContractSerializer


class ContractListView(ListCreateAPIView):
    permission_classes = (IsAuthenticated)
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = ContractSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ContractDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated)
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def get_item(self, id):
        try:
            return Contract.objects.get(id=id)
        except Contract.DoesNotExist:
            raise ValidationError({'error': 'Contract does not exist'})

    def retrieve(self, request, id):
        contract = self.get_item(id)
        serialzer = self.serializer_class(contract)
        return Response({
            'status': 'Ok',
            'data': serialzer.data
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