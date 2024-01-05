from django.urls import path
from organizations.views.web import OrganizationsView, OrganizationDataView, OrganizationDetailView

app_name = 'organizations-web'

urlpatterns = [
    path('', OrganizationsView.as_view(), name='organizations'),
    path('data', OrganizationDataView.as_view(), name='organizations-data'),
    path('<pk>/', OrganizationDetailView.as_view(), name='organization-details'),
]
