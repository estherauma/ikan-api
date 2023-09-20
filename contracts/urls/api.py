from django.urls import path
from contracts.views.api import ContractListView, ContractDetailsView

app_name = 'contracts'

urlpatterns = [
    path('contracts', ContractListView.as_view(), name='contract-list'),
    path('contracts/<int:pk>', ContractDetailsView.as_view(), name='contract-detail'),
]
