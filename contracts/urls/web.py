from django.urls import path
from contracts.views.web import ContractsView, ContractsDataView

app_name = 'contracts-web'
urlpatterns = [
    path('', ContractsView.as_view(), name='contracts'),
    path('data', ContractsDataView.as_view(), name='contracts-data')
]
