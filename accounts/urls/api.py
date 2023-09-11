from django.urls import path
from ..views.api import (
    LoginView,
    RegisterView,
    RequestPasswordReset,
    ResetPassword,
    PasswordResetCheckToken,
    verify_email,
    verify_email_success,
    verify_email_failure,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify-email'),
    path('verify-email-success', verify_email_success, name='verify-email-success'),
    path('verify-email-failure', verify_email_failure, name='verify-email-failure'),
    path('reset-password-request/', RequestPasswordReset.as_view(), name='reset-password-request'),
    path('reset-password-token/', PasswordResetCheckToken.as_view(), name='reset-password-token'),
    path('reset-password/', ResetPassword.as_view(), name='reset-password'),
]
