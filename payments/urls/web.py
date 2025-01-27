from django.urls import path
from payments.views.web import (
    PaymentListView,
    PaymentDetailView,
    AddPayment,
    SelectVessel
)

app_name = "payments"

urlpatterns = [
    path("", PaymentListView.as_view(), name="payments-list"),
    path("<pk>/", PaymentDetailView.as_view(), name="payment-details"),
    path("select-vessel", SelectVessel.as_view(), name='select-vessel'),
    path("add-payments", AddPayment.as_view(), name="add-payments"),
]
