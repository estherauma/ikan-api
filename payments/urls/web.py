from django.urls import path
from payments.views.web import PaymentUploadView, PaymentListView

app_name = 'payments'

urlpatterns = [
    path('', PaymentListView.as_view(), name='payments-list'),
    path('upload', PaymentUploadView.as_view(), name='upload-payments'),
]
