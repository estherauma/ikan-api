from django.urls import path

from dashboards.views import (
    VesselOwnerDashboard, BuyerDashboard, WorkerDashboard, AgentDashboard)
app_name = 'dashboards'

urlpatterns = [
    path('vessel-owner', VesselOwnerDashboard.as_view(), name='vesselowner-dashboard'),
    path('buyer', BuyerDashboard.as_view(), name='buyer-dashboard'),
    path('worker', WorkerDashboard.as_view(), name='worker-dashboard'),
    path('agent', AgentDashboard.as_view(), name='agent-dashboard')

]