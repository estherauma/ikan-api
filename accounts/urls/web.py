from django.urls import path
from accounts.views.web import invite_user, logout_user
from accounts.views.web import \
    UserListView, RegisterWebView, RegisterSuccess, \
    RequestPasswordReset, ResetPassword, LoginView, \
    ResendAcessCode, UserDetailView

app_name = 'accounts'

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('request-password-reset', RequestPasswordReset.as_view(), name='request-password-reset'),
    path('reset-password', ResetPassword.as_view(), name='reset-password'),
    path('users', UserListView.as_view(), name='users'),
    path('users/<pk>/', UserDetailView.as_view(), name='user-details'),
    path('users/invite', invite_user, name='invite-user'),
    path('users/resend-access-code', ResendAcessCode.as_view(), name='resend-access-code'),
    path('register', RegisterWebView.as_view(), name='web-register'),
    path('register-success', RegisterSuccess.as_view(), name='register-success'),
    path("logout", logout_user, name="logout"),
    path("profile/<pk>/", UserDetailView.as_view(), name="profile"),
]
