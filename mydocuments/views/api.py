from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from mydocuments.models import Document, Passport
from mydocuments.serializers import DocumentSerializer, PassportSerializer
from django.utils.dateparse import parse_datetime


class DocumentApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()

    def list(self, request):
        request.data.pop('id', None)
        super_user = self.request.user.is_superuser
        documents = self.get_queryset() if super_user else Document.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(documents, many=True)
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


class DocumentApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()

    def get_document(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return Document.objects.get(id=id)
            else:
                return Document.objects.get(id=id, created_by=req.user.id)
        except Document.DoesNotExist:
            raise ValidationError('Document does not exist')

    def retrieve(self, request, id):
        document = self.get_document(req=request, id=id)
        serializer = self.serializer_class(document)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        document = self.get_document(req=request, id=id)
        serializer = self.serializer_class(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, id):
        document = self.get_document(req=request, id=id)
        user_id = request.user.id

        if user_id != document.created_by:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        document.delete()
        return Response({
            'status': 'OK',
            'message': 'Document deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class PassportApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = PassportSerializer
    queryset = Passport.objects.all()

    def list(self, request):
        request.data.pop('id', None)
        super_user = self.request.user.is_superuser
        passports = self.get_queryset() if super_user else Passport.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(passports, many=True)
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


class PassportApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = PassportSerializer
    queryset = Passport.objects.all()

    def get_passport(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return Passport.objects.get(id=id)
            else:
                return Passport.objects.get(id=id, created_by=req.user.id)
        except Passport.DoesNotExist:
            raise ValidationError('Passport does not exist')

    def retrieve(self, request, id):
        passport = self.get_passport(req=request, id=id)
        serializer = self.serializer_class(passport)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        passport = self.get_passport(req=request, id=id)
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > passport.updated_at:
            serializer = self.serializer_class(passport, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user.id)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(passport).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        passport = self.get_passport(req=request, id=id)
        user_id = request.user.id

        if user_id != passport.created_by:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        passport.delete()
        return Response({
            'status': 'OK',
            'message': 'Passport deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
