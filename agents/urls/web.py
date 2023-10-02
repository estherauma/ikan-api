from django.urls import path
from agents.views.web import AgentsView, AgentsDataView

app_name = 'agents-web'
urlpatterns = [
  path('', AgentsView.as_view(), name='agents'),
  path('data', AgentsDataView.as_view(), name='agents-data')
]
