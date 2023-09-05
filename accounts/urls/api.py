from django.urls import path
from ..views.api import (
    LoginView,
    RegisterView,
    verify_email,
    verify_email_success,
    verify_email_failure,
    VerifyAndSetPassword,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify-email'),
    path('verify-email-success', verify_email_success, name='verify-email-success'),
    path('verify-email-failure', verify_email_failure, name='verify-email-failure'),
    path('verify-access-token', VerifyAndSetPassword.as_view(), name='verify-access-token'),
]   
