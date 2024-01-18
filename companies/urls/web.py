from django.urls import path
from companies.views.web import CompaniesView, CompaniesDataView, CompaniesDetailView

app_name = 'companies-web'

urlpatterns = [
    path('', CompaniesView.as_view(), name='companies'),
    path('data', CompaniesDataView.as_view(), name='companies-data'),
    path('<pk>/', CompaniesDetailView.as_view(), name='company-details'),
]
