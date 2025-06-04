from django.urls import path
from contracts.views.web import (
    ContractsView,
    ContractsDetailView,
    ContractsDataView,
    ContractAccessView,
    AddContractView
)

app_name = 'contracts-web'
urlpatterns = [
    path('', ContractsView.as_view(), name='contracts'),
    path('data', ContractsDataView.as_view(), name='contracts-data'),
    path('<pk>/', ContractsDetailView.as_view(), name='contract-details'),
    path('<pk>/access', ContractAccessView.as_view(), name='contract-access'),
    path('new-contract', AddContractView.as_view(), name='new-contract'),
]
