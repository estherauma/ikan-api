from django.urls import path
from accounts.views.web import login, request_password_reset, reset_password
from accounts.views.web import UserListView, invite_user


urlpatterns = [
    path('login', login, name='login'),
    path('request-password-reset', request_password_reset, name='request-password-reset'),
    path('reset-password', reset_password, name='reset-password'),
    path('users', UserListView.as_view(), name='users'),
    path('users/invite', invite_user, name='invite-user')
]
