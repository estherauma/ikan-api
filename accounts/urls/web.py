from django.urls import path
from accounts.views.web import login
from accounts.views.web import \
    UserListView, RegisterWebView, RegisterSuccess, \
    RequestPasswordReset, ResetPassword


urlpatterns = [
    path('login', login, name='login'),
    path('request-password-reset', RequestPasswordReset.as_view(), name='request-password-reset'),
    path('reset-password', ResetPassword.as_view(), name='reset-password'),
    path('users', UserListView.as_view(), name='users'),
    path('register', RegisterWebView.as_view(), name='web-register'),
    path('register-success', RegisterSuccess.as_view(), name='register-success'),
]
