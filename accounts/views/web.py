from django.shortcuts import render
from django.views.generic.list import ListView

# models
from accounts.models import User


def get_base(request):
    return render(request, template_name="themes/v1/base.html")

def login(request):
    return render(request, template_name="login.html")

def request_password_reset(request):
    return render(request, template_name='password-reset/request-password-reset.html')

def reset_password(request):
    return render(request, template_name='password-reset/reset-password.html')


class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'user-list.html'
