from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from survey.models import Survey, InlineQuestion
from survey.serializers import SurveySerializer, InLineQuestionSerializer


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


class InlineQuestionApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = InLineQuestionSerializer
    queryset = InlineQuestion.objects.all()

    def list(self, request):
        super_user = self.request.user.is_superuser
        inline_questions = self.get_queryset() if super_user \
            else InlineQuestion.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(inline_questions, many=True)

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
        serializer.save(created_by=request.user.id, updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class InlineQuestionApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = InLineQuestionSerializer
    queryset = InlineQuestion.objects.all()

    def get_inline_question(self, req, id):
        try:
            super_user = self.request.user.is_superuser
            if super_user:
                return InlineQuestion.objects.get(id=id)
            else:
                return InlineQuestion.objects.get(id=id, created_by=req.user.id)
        except InlineQuestion.DoesNotExist:
            raise ValidationError('Inline question does not exist')

    def retrieve(self, request, id):
        inline_question = self.get_inline_question(req=request, id=id)
        serializer = self.serializer_class(inline_question)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        inline_question = self.get_inline_question(req=request, id=id)
        serializer = self.serializer_class(inline_question, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def destroy(self, request, id):
        inline_question = self.get_inline_question(req=request, id=id)
        inline_question.delete()
        return Response({
            'status': 'OK',
            'message': 'Inline question deleted successfully'
        }, status.HTTP_200_OK)
