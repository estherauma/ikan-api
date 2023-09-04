from typing import Any, Dict
from accounts.forms import InviteUser
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
from accounts.forms import RegistrationForm
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from common.email import TunaEmailHelper, EmailTemplate
from common.access_code import get_access_code
from django.contrib import messages

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
    print(request.method)
    if request.method == 'POST':
        form = InviteUser(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data.get('email'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                is_active=False,
                # generate random access code
                access_code=get_access_code()
            )
            # Send verification email with access code
            email = TunaEmailHelper()
            success = email.tuna_send_email(
                to_emails=[user.email],
                subject='Your IKAN access token',
                body={
                    'first_name': user.first_name,
                    'access_token': user.access_code,
                }
            )
            if success:
                 messages.success(request, 'Your message was sent successfully.')
            else:
                 messages.error(request, 'An error occurred while sending the user an email.')
            return redirect('/account/users')

def reg(request):
    return render(request, template_name='register.html')


def register_success(request):
    return render(request, template_name="register-success.html")


class RegisterWebView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(data=request.POST)

        if not form.is_valid():
            return render(request, 'register.html', {'form': form})

        user = User.objects.create_user(
            email=form.cleaned_data.get('email'),
            password=form.cleaned_data.get('password1'),
            first_name=form.cleaned_data.get('first_name'),
            last_name=form.cleaned_data.get('last_name'),
            is_active=False
        )
        email_helper = TunaEmailHelper()
        try:
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject='Your IKAN access token',
                body={
                    'first_name': user.first_name,
                    'access_token': user.access_code,
                },
                template=EmailTemplate.VERIFY_EMAIL.value,
            )
        except Exception as e:
            print(e)
            print('Email sending failed')
       

        # Send verification email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f'{config("BASE_URL")}/api/v1/accounts/verify-email/{uid}/{token}'
        email_helper = TunaEmailHelper()
        email_helper.tuna_send_email(
            to_emails=[user.email],
            subject='Verify your email to start using IKAN',
            body={
                'first_name': user.first_name,
                'verification_link': verification_link,
            },
            template=EmailTemplate.VERIFY_EMAIL.value,
        )
        # messages.success(request, 'Account created successfully. Please check your email to verify your account.')

        return redirect('/account/register-success')
