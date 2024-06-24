from django.urls import path
from survey.views.api import SurveyApiDetailView, SurveyApiListView, \
    InlineQuestionApiListView, InlineQuestionApiDetailView

app_name = 'survey'

urlpatterns = [
    path('surveys', SurveyApiListView.as_view(), name='survey-list'),
    path('surveys/<str:id>', SurveyApiDetailView.as_view(), name='survey-detail'),
    path('inline-questions', InlineQuestionApiListView.as_view(), name='inline-question-list'),
    path('inline-questions/<str:id>', InlineQuestionApiDetailView.as_view(), name='inline-question-detail'),
]
