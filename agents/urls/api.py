from django.urls import path
from agents.views.api import AgentApiDetailView, AgentsApiListView

app_name = 'agents'

urlpatterns = [
    path('agents', AgentsApiListView.as_view(), name='agent-list'),
    path('agents/<int:id>', AgentApiDetailView.as_view(), name='agent-detail'),
]
