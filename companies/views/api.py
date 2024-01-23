from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from companies.models import Company
from companies.serializers import CompanySerializer


class CompanyApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def list(self, request):
        super_user = self.request.user.is_superuser
        companies = self.get_queryset() if super_user else Company.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(companies, many=True)
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


class CompanyApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_company(self, req, id):
        try:

            super_user = self.request.user.is_superuser
            if super_user:
                return Company.objects.get(app_ref=id, created_by=req.user.id)
            else:
                return Company.objects.get(app_ref=id)
        except Company.DoesNotExist:
            raise ValidationError('Company does not exist')

    def retrieve(self, request, id):
        company = self.get_company(req=request, id=id)
        serializer = self.serializer_class(company)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        company = self.get_company(req=request, id=id)
        serializer = self.serializer_class(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        company = self.get_company(req=request, id=id)
        user_id = request.user.id

        if user_id != company.created_by.id:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        company.delete()
        return Response({
            'status': 'OK',
            'data': id
        }, status.HTTP_200_OK)
