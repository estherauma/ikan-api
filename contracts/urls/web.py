from django.urls import path
from companies.views.web import ContractAccessView
from contracts.views.web import *

app_name = 'contracts-web'
urlpatterns = [
    path('', ContractsView.as_view(), name='contracts'),
    path('data', ContractsDataView.as_view(), name='contracts-data'),
    path('<pk>/', ContractsDetailView.as_view(), name='contract-details'),
    path('<pk>/access', ContractAccessView.as_view(), name='contract-access'),
]
