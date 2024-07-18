from django.urls import path
from survey.views.web import SurveyView, SurveyDataView, QuestionResponseDetailView, \
    TFAVideoDataView, InlineQuestionDataView

app_name = 'surveys-web'

urlpatterns = [
    path('', SurveyView.as_view(), name='surveys'),
    path('data/', SurveyDataView.as_view(), name='survey-data'),
    path('tfa-video/', SurveyView.as_view(), name='tfa-video'),
    path('tfa-video/data/', TFAVideoDataView.as_view(), name='tfa-video-data'),
    path('tfa-video/<str:question_key>/', QuestionResponseDetailView.as_view(), name='tfa-video-detail'),
    path('inline-questions/', SurveyView.as_view(), name='inline-questions'),
    path('inline-questions/data/', InlineQuestionDataView.as_view(), name='inline-questions-data'),
    path('inline-questions/<str:question_key>/', QuestionResponseDetailView.as_view(), name='inline-question-detail'),
    path('<str:question_key>/', QuestionResponseDetailView.as_view(), name='survey-response-details'),
]
