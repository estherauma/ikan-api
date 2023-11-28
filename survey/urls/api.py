from django.urls import path
from survey.views.api import SurveyApiDetailView, SurveyApiListView

app_name = 'survey'

urlpatterns = [
    path('surveys', SurveyApiListView.as_view(), name='survey-list'),
    path('surveys/<int:id>', SurveyApiDetailView.as_view(), name='survey-detail')
]
