from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from survey.models import Survey
from survey.serializers import SurveySerializer

class SurveyApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = SurveySerializer
    queryset = Survey.objects.all()

    def list(self, request):
        super_user = self.request.user.is_superuser
        surveys = self.get_queryset() if super_user else Survey.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(surveys, many=True)
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


class SurveyApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = SurveySerializer
    queryset = Survey.objects.all()

    def get_survey(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return Survey.objects.get(id=id)
            else:
                 return Survey.objects.get(id=id, created_by=req.user.id)
        except Survey.DoesNotExist:
            raise ValidationError('Survey does not exist')

    def retrieve(self, request, id):
        survey = self.get_survey(req=request, id=id)
        serializer = self.serializer_class(survey)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        survey = self.get_survey(req=request, id=id)
        serializer = self.serializer_class(survey, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def destroy(self, request, id):
        survey = self.get_survey(req=request, id=id)
        survey.delete()
        return Response({
            'status': 'OK',
            'message': 'Survey deleted successfully'
        }, status.HTTP_200_OK)
