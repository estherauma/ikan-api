from typing import Any, Dict
from django.shortcuts import render
from django.views.generic.list import ListView
from accounts.forms import InviteUser

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite_user_form'] = InviteUser()
        return context

def invite_user(request):
    if request.method == 'POST':
        form = InviteUser(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data.get('email'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                is_active=False
            )

            