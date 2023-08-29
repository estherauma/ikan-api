from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
from accounts.forms import RegistrationForm
from rest_framework.response import Response
from rest_framework import status, serializers
from accounts.serializers import RegisterSerializer
from django.contrib import messages
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
import requests
from django.template.loader import render_to_string
from common.email import TunaEmailHelper, EmailTemplate

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


def reg(request):
    return render(request, template_name='register.html')


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

        # Send verification email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f'{config("BASE_URL")}/api/v1/accounts/verify-email/{uid}/{token}'

        # Using send_mail
        # email_helper = TunaEmailHelper()
        # email_helper.tuna_send_email(
        #     to_emails=[user.email],
        #     subject='Verify your email to start using Ikan',
        #     body={
        #         'first_name': user.first_name,
        #         'verification_link': verification_link,
        #     },
        #     template=EmailTemplate.VERIFY_EMAIL.value,
        # )

        # Using mailgun
        template = EmailTemplate.VERIFY_EMAIL.value
        body = {
            'first_name': user.first_name,
            'verification_link': verification_link,
        }
        print('verification_link.......', verification_link)
        requests.post(
                    f"{config('MAILGUN_BASE_URL')}/messages",
                    auth=("api", config('MAILGUN_API_KEY')),
                    data={"from": config("APPLICATION_FROM_EMAIL"),
                          "to": user.email,
                          "subject": "Verify your email to start using Ikan",
                          "html": render_to_string(f'emails/{template}', {"body": body})
                          }
                    )
        # messages.success(request, 'Account created successfully. Please check your email to verify your account.')

        return redirect('/account/login')
