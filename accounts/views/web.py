from accounts.forms import InviteUser, ResendTokenForm
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
from accounts.forms import RegistrationForm, PasswordResetForm, RequestPasswordResetForm
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from common.email import TunaEmailHelper, EmailTemplate
import random
from common.utils import get_access_code
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group

# models
from accounts.models import User

# forms
from accounts.forms import LoginForm


@login_required(login_url='/account/login')
def get_base(request):
    return render(request, template_name="themes/v1/base.html")


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        context = {'form': form}
        return render(request, template_name='login.html', context=context)

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                messages.error(request, "Can not log in with provided credentials!")
                # go back to login page
                return render(request, template_name='login.html')
        else:
            messages.error(request, "Error validating form!")
            return render(request, template_name='login.html')


def request_password_reset(request):
    return render(request, template_name='password-reset/request-password-reset.html')


def reset_password(request):
    return render(request, template_name='password-reset/reset-password.html')


class UserListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = 'users'
    template_name = 'user-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite_user_form'] = InviteUser()
        context['page_title'] = 'User List'
        context['resend_token_form'] = ResendTokenForm()
        return context


@login_required(login_url='/account/login')
def invite_user(request):
    if request.method == 'POST':
        form = InviteUser(request.POST)
        if form.is_valid():
            user_exists = User.objects.filter(email=form.cleaned_data.get('email')).exists()
            if not user_exists:
                user = User.objects.create_user(
                    email=form.cleaned_data.get('email'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    is_active=False,
                    access_code=get_access_code()
                )
                # Save user group/role
                group = Group.objects.get(name=form.cleaned_data.get('role'))
                user.groups.add(group)

                # Send verification email with access code
                email = TunaEmailHelper()
                success = email.tuna_send_email(
                    to_emails=[user.email],
                    subject='Your IKAN access token',
                    body={
                        'email': user.email,
                        'access_token': user.access_code,
                    },
                    template=EmailTemplate.ACCESS_TOKEN.value,
                )
                if success:
                    messages.success(request, 'Your message was sent successfully.')
                else:
                    messages.error(request, 'An error occurred while sending the user an email.')
            else:
                user = User.objects.get(email=form.cleaned_data.get('email'))
                if not user.is_active:
                    messages.info(request, 'User already exists. Please resend invite token.')
                else:
                    messages.info(request, 'User already exists.')

            return redirect('/account/users')


class ResendAcessCode(View):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        user = User.objects.get(pk=pk)
        context['form'] = ResendTokenForm()
        context['user'] = user
        return context

    def get(self, request):
        form = ResendTokenForm()
        return render(request, 'user-list.html', {'form': form})

    def post(self, request):
        form = ResendTokenForm(data=request.POST)

        if form.is_valid():
            user = User.objects.get(email=form.cleaned_data.get('email'))
            user.access_code = get_access_code()
            user.save()

            # Send verification email with access code
            email = TunaEmailHelper()
            success = email.tuna_send_email(
                to_emails=[user.email],
                subject='Your IKAN access token',
                body={
                    'email': user.email,
                    'access_token': user.access_code,
                },
                template=EmailTemplate.ACCESS_TOKEN.value,
            )
            if success:
                messages.success(request, 'The access code was resent successfully.')
            else:
                messages.error(request, 'An error occurred while resending the user acess code.')

            return redirect('/account/users')


class Reg(View):
    def get(request):
        return render(request, template_name='register.html')


class RegisterSuccess(View):
    def get(request):
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
        messages.success(request, 'Account created successfully. Please check your email to verify your account.')

        return redirect('/account/register-success')


class RequestPasswordReset(View):
    def get(self, request):
        form = RequestPasswordResetForm()
        return render(request, template_name='password-reset/request-password-reset.html', context={'form': form})

    def post(self, request):
        form = RequestPasswordResetForm(data=request.POST)
        if not form.is_valid():
            return render(request, template_name='password-reset/request-password-reset.html', context={'form': form})

        user = User.objects.get(email=form.cleaned_data.get('email'))
        if user:
            password_rest_token = random.randrange(11111, 99999,)
            user.reset_password_token = password_rest_token
            user.save()

            email_helper = TunaEmailHelper()
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject='Reset your IKAN password',
                body={
                    'first_name': user.first_name,
                    'password_rest_token': password_rest_token,
                },
                template=EmailTemplate.PASSWORD_RESET_REQUEST.value,
            )
            messages.success(request, 'Please check your email for the password reset code.')
            return redirect('reset-password')
        else:
            messages.error(request, 'Invalid email address.')
            return render(request, template_name='password-reset/request-password-reset.html', context={'form': form})


class ResetPassword(View):
    def get(self, request):
        form = PasswordResetForm()
        return render(request, template_name='password-reset/reset-password.html', context={'form': form})

    def post(self, request):
        form = PasswordResetForm(data=request.POST)
        if not form.is_valid():
            return render(request, template_name='password-reset/reset-password.html', context={'form': form})

        user = User.objects.get(email=form.cleaned_data.get('email'))
        if user:
            user.set_password(form.cleaned_data.get('password1'))
            user.reset_password_token = None
            user.save()
            messages.success(request, 'Password reset successfully. Please login with your new password.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid email address.')
            return render(request, template_name='password-reset/reset-password.html', context={'form': form})


@login_required
def logout_user(request):
    logout(request)
    return redirect("/account/login")
