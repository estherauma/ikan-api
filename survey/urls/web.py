from django.urls import path
from survey.views.web import SurveyView, SurveyDataView

app_name = 'surveys-web'

urlpatterns = [
    path('', SurveyView.as_view(), name='surveys'),
    path('data', SurveyDataView.as_view(), name='survey-data')
]