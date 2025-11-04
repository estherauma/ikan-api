from django.urls import path
from companies.views.api import CompanyApiDetailView, CompanyApiListView

app_name = 'companies'

urlpatterns = [
    path('companies', CompanyApiListView.as_view(), name='company-list'),
    path('companies/<str:id>', CompanyApiDetailView.as_view(), name='company-detail'),
]
