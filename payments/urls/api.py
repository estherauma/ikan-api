from django.urls import path
from payments.views.api import PaymentApiListView


app_name = 'api-payments'

urlpatterns = [
    path('payments/', PaymentApiListView.as_view(), name='payments-list'),
    path('payments/<pk>/', PaymentApiListView.as_view(), name='payment-detail'),
]
