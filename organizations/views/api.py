# rest_framework imports
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from organizations.models import Organization

from organizations.serializers import OrganizationSerializer


class OrganizationListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated,])
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

class OrganizationDetailsView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated])
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()

    def get_organization(self, req, id):
        try:
            return Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            raise ValidationError({'error': 'Organization does not exist'})
        
    def retrieve(self, request, id):
        organization = self.get_organization(id)
        serializer = self.serializer_class(organization)
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