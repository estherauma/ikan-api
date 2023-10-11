from django.urls import path
from organizations.views.api import OrganizationListView, OrganizationDetailsView

app_name = 'organizations'

urlpatterns = [
    path('organizations', OrganizationListView.as_view(), name='organization-list'),
    path('organizations/<int:pk>', OrganizationDetailsView.as_view(), name='organization-detail')
]