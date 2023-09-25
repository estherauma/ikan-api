from django.urls import path
from contracts.views.api import ContractClauseListView, ContractListView, ContractDetailsView

app_name = 'contracts'

urlpatterns = [
    path('contracts', ContractListView.as_view(), name='contract-list'),
    path('contracts/<int:pk>', ContractDetailsView.as_view(), name='contract-detail'),
    path('contracts/clauses', ContractClauseListView.as_view(), name='contract-clause-list'),
    path('contracts/clauses/<int:pk>', ContractClauseListView.as_view(), name='contract-clause-detail')
]
