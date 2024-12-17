from django.urls import path
from payments.views.api import PaymentApiListView


app_name = 'api-payments'

urlpatterns = [
    path('', PaymentApiListView.as_view(), name='payments-list'),
    path('<pk>/', PaymentApiListView.as_view(), name='payment-detail'),
]
