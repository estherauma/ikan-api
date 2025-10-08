from accounts.forms import InviteUser, ResendTokenForm, CreateWorkerForVOForm
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
from django.views.generic import DetailView
from prismic.utils import PrismicUtils
from accounts.models import User
from accounts.forms import LoginForm


@login_required(login_url='/account/login')
def get_base(request):
    return render(request, template_name="themes/v1/base.html")


def loggedin_user(request):
    """
    Resultant object is passed to the context processor
    """
    prismic_utils = PrismicUtils(request)
    loggedin_user = None
    show_users_menu_item = False

    if request.user.is_authenticated:
        loggedin_user = request.user
        loggedin_user.is_vessel_owner = False
        loggedin_user.is_worker = False
        loggedin_user.is_public = False

        roles = loggedin_user.groups.all().values_list('name', flat=True)
        if 'vessel_owner' in roles:
            show_users_menu_item = True
            loggedin_user.is_vessel_owner = True
        elif 'worker' in roles:
            loggedin_user.is_worker = True
        elif 'public' in roles:
            loggedin_user.is_public = True

    return {
            'loggedin_user': loggedin_user,
            'show_users_menu_item': show_users_menu_item,
            'selected_language': request.session.get('language', 'en-us'),
            'common_text': prismic_utils.common_text,
            'menu_labels': prismic_utils.get_menu_labels(),
        }


class LoginView(View):
    def get_context_data(self, **kwargs):
        context = kwargs
        context['form'] = LoginForm()

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, template_name='login.html', context=context)

    def post(self, request):
        context = self.get_context_data()
        form = LoginForm(data=request.POST)
        context = {'form': form}
        if form.is_valid():
            email_or_phone = form.cleaned_data.get("email_or_phone")
            password = form.cleaned_data.get("password")

            user = authenticate(request, email_or_phone=email_or_phone, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                unverified_number_err = getattr(request, 'unverified_number_err', None)
                if unverified_number_err:
                    messages.error(request,  unverified_number_err)
                else:
                    messages.error(request, "Can not log in with provided credentials!")

                # go back to login page
                return render(request, template_name='login.html', context=context)
        else:
            messages.error(request, "Error validating form!")
            return render(request, template_name='login.html', context=context)


class UserListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = 'users'
    template_name = 'user-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite_user_form'] = InviteUser()
        context['resend_token_form'] = ResendTokenForm()

        super_user = self.request.user.is_superuser
        users = self.get_queryset() if super_user else User.objects.filter(created_by=self.request.user.id)
        context['users'] = users

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        prof_form_labels = prismic_utils.get_field_labels_from_form_questions(None, 'vo-agent-buyer-profile-form')
        reg_form_labels = prismic_utils.get_field_labels_from_form_questions(None, 'registration-details-form')
        form_labels = {
            **prof_form_labels,
            **reg_form_labels,
        }
        context['form_labels'] = form_labels
        return context


class WorkersListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = 'workers'
    template_name = 'worker-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite_user_form'] = InviteUser()
        context['resend_token_form'] = ResendTokenForm()
        context['create_worker_for_vo_form'] = CreateWorkerForVOForm(user=self.request.user)

        super_user = self.request.user.is_superuser
        users = self.get_queryset() if super_user else User.objects.filter(created_by=self.request.user.id)
        workers = users.filter(groups__name='worker', created_by=self.request.user.id)

        context['workers'] = workers
        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        return context

    # Method creates workers only. Should be modified for other roles
    def post(self, request):
        self.object_list = self.get_queryset()
        form = CreateWorkerForVOForm(data=request.POST, user=request.user)
        context = self.get_context_data()
        context['create_worker_for_vo_form'] = form
        if form.is_valid():
            user_exists = User.objects.filter(email=form.cleaned_data.get('email')).exists()
            if not user_exists:
                user = User.objects.create_user(
                    email=form.cleaned_data.get('email'),
                    password=form.cleaned_data.get('password1'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    is_active=True,
                    created_by=form.cleaned_data.get('vessel_owner', request.user),
                    updated_by=form.cleaned_data.get('vessel_owner', request.user),
                )
                # Save user group/role
                group = Group.objects.get(name='worker')
                user.groups.add(group)

                # Sending verification email is disabled for workers created by superusers for VOs
                # # Send verification email with access code
                # email = TunaEmailHelper()
                # success = email.tuna_send_email(
                #     to_emails=[user.email],
                #     subject='Your IKAN access token',
                #     body={
                #         'email': user.email,
                #         'access_token': user.access_code,
                #     },
                #     template=EmailTemplate.ACCESS_TOKEN.value,
                # )
                # if success:
                #     messages.success(request, 'Worker created successfully.')
                # else:
                #     messages.error(request, 'An error occurred while sending the user an email.')
                messages.success(request, 'Worker created successfully.')
            else:
                messages.info(request, 'User already exists.')
                return render(request, 'worker-list.html', context)

            return redirect('accounts:workers')
        else:
            messages.error(request, 'Error validating form!')
            return render(request, 'worker-list.html', context)


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


class RegisterSuccess(View):
    def get(self, request):
        prismic_utils = PrismicUtils(request)
        context = {
            'reg_success_page_text': prismic_utils.get_page_text('signup-sucess'),  # Ignore typo
            }
        return render(request, template_name="register-success.html", context=context)


class RegisterWebView(View):
    def get_context_data(self, **kwargs):
        context = kwargs

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        context['form'] = RegistrationForm(auth_common_text=auth_common_text)
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, 'register.html', context)

    def post(self, request):
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        form = RegistrationForm(data=request.POST, auth_common_text=auth_common_text)
        context['form'] = form

        if not form.is_valid():
            return render(request, 'register.html', context)

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
            subject=auth_common_text.get('verifyYourEmailToStartUsingIKAN', 'Verify your email to start using IKAN'),
            body={
                'first_name': user.first_name,
                'verification_link': verification_link,
            },
            template=EmailTemplate.VERIFY_EMAIL.value,
        )
        messages.success(request, 'Account created successfully. Please check your email to verify your account.')

        return redirect('/account/register-success')


class RequestPasswordReset(View):
    def get_context_data(self, **kwargs):
        context = kwargs

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        context['form'] = RequestPasswordResetForm(auth_common_text=auth_common_text)
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, template_name='password-reset/request-password-reset.html', context=context)

    def post(self, request):
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        form = RequestPasswordResetForm(data=request.POST, auth_common_text=auth_common_text)
        context['form'] = form
        if not form.is_valid():
            return render(request, template_name='password-reset/request-password-reset.html', context=context)

        user = User.objects.get(email=form.cleaned_data.get('email'))
        if user:
            password_rest_token = random.randrange(11111, 99999,)
            user.reset_password_token = password_rest_token
            user.save()

            email_helper = TunaEmailHelper()
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject=auth_common_text.get('resetYourPassword', 'Reset your IKAN password'),
                body={
                    'first_name': user.first_name,
                    'password_rest_token': password_rest_token,
                },
                template=EmailTemplate.PASSWORD_RESET_REQUEST.value,
            )
            messages.success(request, auth_common_text.get(
                'passwordResetRequestSentMessage', 'Please check your email for the password reset code.'))
            return redirect('reset-password')
        else:
            messages.error(request, auth_common_text.get('invalidEmailAddress', 'Invalid email address.'))
            return render(request, template_name='password-reset/request-password-reset.html', context=context)


class ResetPassword(View):
    def get_context_data(self, **kwargs):
        context = kwargs

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        context['form'] = PasswordResetForm(auth_common_text=auth_common_text)
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, template_name='password-reset/reset-password.html', context=context)

    def post(self, request):
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        form = PasswordResetForm(data=request.POST, )
        context['form'] = form
        if not form.is_valid():
            return render(request, template_name='password-reset/reset-password.html', context={'form': form})

        user = User.objects.get(email=form.cleaned_data.get('email'))
        if user:
            user.set_password(form.cleaned_data.get('password1'))
            user.reset_password_token = None
            user.save()
            messages.success(request, auth_common_text.get(
                'passwordResetSuccessMessage', 'Password reset successfully. Please login with your new password.'))
            return redirect('login')
        else:
            messages.error(request, auth_common_text.get('invalidEmailAddress', 'Invalid email address.'))
            return render(request, template_name='password-reset/reset-password.html', context={'form': form})


@login_required
def logout_user(request):
    logout(request)
    return redirect("/account/login")


@login_required
def select_language(request):
    if request.method == 'POST':
        lang = request.POST.get('language')
        if lang:
            request.session['language'] = lang
            return redirect('/')

    return render(request, 'select_language.html')


@login_required
def change_language(request):
    if request.method == 'POST':
        lang = request.POST.get('language')
        if lang:
            request.session['language'] = lang
            return redirect('/')

    prismic_utils = PrismicUtils(request)
    auth_common_text = prismic_utils.get_page_text('auth-common-text')
    context = {
        'auth_common_text': auth_common_text,
    }
    return render(request, 'change_language.html', context)
