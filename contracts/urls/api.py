from django.urls import path
from contracts.views.api import ContractClauseListView, ContractListView, ContractDetailsView, \
    ContractDocumentListView, ContractDocumentDetailsView, ContractClauseDetailsView


app_name = 'contracts'

urlpatterns = [
    path('contracts/', ContractListView.as_view(), name='contract-list'),
    path('contracts/<str:id>', ContractDetailsView.as_view(), name='contract-detail'),
    path('contracts-clauses', ContractClauseListView.as_view(), name='contract-clause-list'),
    path('contracts-clauses/<str:id>', ContractClauseDetailsView.as_view(), name='contract-clause-detail'),
    path('contracts-documents', ContractDocumentListView.as_view(), name='contract-document-list'),
    path('contracts-documents/<str:id>', ContractDocumentDetailsView.as_view(), name='contract-document-detail'),
]
