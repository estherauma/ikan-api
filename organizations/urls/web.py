from django.urls import path
from organizations.views.web import OrganizationsView, OrganizationDataView

app_name = 'organizations-web'

urlpatterns = [
    path('', OrganizationsView.as_view(), name='organizations'),
    path('data', OrganizationDataView.as_view(), name='organizations-data')
]
