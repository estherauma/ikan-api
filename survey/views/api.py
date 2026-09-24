from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from survey.models import Survey, InlineQuestion, LearningHubProgress
from survey.serializers import SurveySerializer, InLineQuestionSerializer, LearningHubProgressSerializer
from accounts.models import User
from common.utils import generate_uuid
from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime


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
        serializer.save(created_by=request.user)
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
        serializer.save(created_by=request.user, updated_by=request.user)
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
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > inline_question.updated_at:
            serializer = self.serializer_class(inline_question, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status.HTTP_200_OK)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': self.serializer_class(inline_question).data
            }, status.HTTP_200_OK)

    def destroy(self, request, id):
        inline_question = self.get_inline_question(req=request, id=id)
        inline_question.delete()
        return Response({
            'status': 'OK',
            'message': 'Inline question deleted successfully'
        }, status.HTTP_200_OK)


class LearningHubProgressApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get_user(self, request):
        user_id = request.data.get('user')
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
                return user
            except User.DoesNotExist:
                return None
        else:
            return None

    def get(self, request):
        user = self.get_user(request) or request.user
        lb_data = LearningHubProgress.objects.filter(user=user)
        serializer = LearningHubProgressSerializer(lb_data, many=True)

        return Response({
            'status': 'OK',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = self.get_user(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )

        progress_data = request.data.get('progress_data')
        app_ref = request.data.get('app_ref', generate_uuid())
        created_by = request.data.get('created_by', request.user.id)
        updated_by = request.data.get('updated_by', request.user.id)
        created_at = request.data.get('created_at', None)
        updated_at = request.data.get('updated_at', None)
        if not isinstance(progress_data, list):
            return Response({'error': 'Invalid format'}, status=400)

        serializer_data = {**request.data}
        serializer = LearningHubProgressSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            lb_progress = None
            try:
                lb_progress = LearningHubProgress.objects.order_by('-created_at').first()
            except LearningHubProgress.DoesNotExist:
                lb_progress = None
            if lb_progress:
                req_updated_at = parse_datetime(updated_at) if updated_at else None
                if req_updated_at is None or req_updated_at > lb_progress.updated_at:
                    lb_progress.progress_data = progress_data
                    lb_progress.updated_by = updated_by
                    lb_progress.updated_at = updated_at
                    lb_progress.save()
            else:
                lb_progress = LearningHubProgress.objects.create(
                    app_ref=app_ref,
                    user=user,
                    progress_data=progress_data,
                    created_by=created_by,
                    updated_by=updated_by,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                lb_progress.save()
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
