from django.urls import path
from accounts.views.web import invite_user, logout_user, \
    UserListView, RegisterWebView, RegisterSuccess, \
    RequestPasswordReset, ResetPassword, LoginView, \
    ResendAcessCode, UserDetailView, WorkersListView, change_language, \
    VerifyPhoneNumber, verify_phone_number_success, verify_phone_number_failure, \
    resend_otp, resend_password_reset_token, CreateAgentVesselownerRelationshipView, AccountSetup

app_name = 'accounts'

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('request-password-reset', RequestPasswordReset.as_view(), name='request-password-reset'),
    path('reset-password', ResetPassword.as_view(), name='reset-password'),
    path('setup-account', AccountSetup.as_view(), name='setup-account'),
    path('reset-password/resend-token', resend_password_reset_token, name='resend-password-reset-token'),
    path('users', UserListView.as_view(), name='users'),
    path('users/<pk>/', UserDetailView.as_view(), name='user-details'),
    path('users/invite', invite_user, name='invite-user'),
    path('users/resend-access-code', ResendAcessCode.as_view(), name='resend-access-code'),
    path('register', RegisterWebView.as_view(), name='web-register'),
    path('register-success', RegisterSuccess.as_view(), name='register-success'),
    path("logout", logout_user, name="logout"),
    path("profile/<pk>/", UserDetailView.as_view(), name="profile"),
    path('workers', WorkersListView.as_view(), name='workers'),
    path('change-language', change_language, name='change-language'),
    path('verify-phone-number', VerifyPhoneNumber.as_view(), name='verify-phone-number'),
    path('verify-phone-number/success', verify_phone_number_success, name='verify-phone-number-success'),
    path('verify-phone-number/failure', verify_phone_number_failure, name='verify-phone-number-failure'),
    path('verify-phone-number/resend-otp', resend_otp, name='resend-otp'),
    path('create-agent-vo-relationship', CreateAgentVesselownerRelationshipView.as_view(),
         name='create-agent-vo-relationship'),
]
