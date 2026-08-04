from accounts.forms import InviteUser, ResendTokenForm, CreateWorkerForVOForm, \
    LoginForm, RegistrationForm, PasswordResetForm, RequestPasswordResetForm, \
    CreateAgentVesselownerRelationshipForm
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
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
from accounts.models import User, AgentVesselOwnerRelationship
from common.twilio import OTPVerification, send_verification_code, get_locale_from_request


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
        loggedin_user.is_taiwanese_agent = False
        loggedin_user.is_indonesian_agent = False

        roles = loggedin_user.groups.all().values_list('name', flat=True)
        if 'vessel_owner' in roles:
            show_users_menu_item = True
            loggedin_user.is_vessel_owner = True
        elif 'worker' in roles:
            loggedin_user.is_worker = True
        elif 'public' in roles:
            loggedin_user.is_public = True
        elif 'taiwanese_agent' in roles:
            loggedin_user.is_taiwanese_agent = True
        elif 'indonesian_agent' in roles:
            loggedin_user.is_indonesian_agent = True

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

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['form'] = LoginForm(auth_common_text=auth_common_text)
        context['auth_common_text'] = auth_common_text
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, template_name='login.html', context=context)

    def post(self, request):
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        form = LoginForm(data=request.POST, auth_common_text=auth_common_text)
        context = {**context, 'form': form}
        if form.is_valid():
            email_or_phone = form.cleaned_data.get("email_or_phone")
            password = form.cleaned_data.get("password")

            user = authenticate(request, email_or_phone=email_or_phone, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                # Add translation here
                unverified_number_err = getattr(request, 'unverified_number_err', None)
                if unverified_number_err:
                    user_id = getattr(request, 'user_id', None)
                    context['show_verify_button'] = True
                    request.session['user_id_from_login'] = user_id
                    messages.error(request,  unverified_number_err)
                else:
                    # Add translation here
                    messages.error(request, "Can not log in with provided credentials!")

                # go back to login page
                return render(request, template_name='login.html', context=context)
        else:
            # Add translation here
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
        context['create_agent_vo_relationship_form'] = CreateAgentVesselownerRelationshipForm()

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
        context['show_create_worker_for_VO_modal'] = False
        return context

    # Method creates workers only. Should be modified for other roles
    def post(self, request):
        self.object_list = self.get_queryset()
        form = CreateWorkerForVOForm(data=request.POST, user=request.user)
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        context['create_worker_for_vo_form'] = form
        if form.is_valid():
            recruited_by = None
            if request.user.groups.filter(name='taiwanese_agent').exists() or \
               request.user.groups.filter(name='indonesian_agent').exists():
                recruited_by = request.user
            user = User.objects.create_user(
                email=form.cleaned_data.get('email'),
                mobile=form.cleaned_data.get('mobile'),
                password=form.cleaned_data.get('password1'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                is_active=True,
                created_by=form.cleaned_data.get('vessel_owner', request.user.id),
                updated_by=form.cleaned_data.get('vessel_owner', request.user.id),
                recruited_by=recruited_by,
            )
            # Save user group/role
            group = Group.objects.get(name='worker')
            user.groups.add(group)

            # if form.cleaned_data.get('has_email'):
            #     # Sending verification email is disabled for workers created by superusers for VOs
            #     # Send verification email with access code
            #     email = TunaEmailHelper()
            #     success = email.tuna_send_email(
            #         to_emails=[user.email],
            #         subject='Your IKAN access token',
            #         body={
            #             'email': user.email,
            #             'access_token': user.access_code,
            #         },
            #         template=EmailTemplate.ACCESS_TOKEN.value,
            #         auth_common_text=auth_common_text,
            #     )
            #     if not success:
            #         messages.error(request, 'User created but an error occurred while sending the email. \
            #                        Please contact support.')
            if form.cleaned_data.get('has_phone_number'):
                messages.success(request,
                                 auth_common_text.get('accountCreatedVerifyPhoneNumber',
                                                      'Account created successfully. \
                                                        Please verify your phone number to activate your account.'))
                try:
                    otp_service = OTPVerification()
                    locale = get_locale_from_request(request)
                    send_result = otp_service.send_otp(user.mobile, locale=locale)
                    if not send_result.get('success'):
                        if auth_common_text.get(send_result.get('errorKey')) is not None:
                            messages.error(request, auth_common_text.get(send_result.get('errorKey')))
                        else:
                            messages.error(request, auth_common_text.get('unableToGenerateOTP',
                                                                         'Unable to generate OTP code.'))
                except Exception:
                    messages.error(request, auth_common_text.get('otpCodeSendError',
                                                                 'An error occurred while sending OTP code.'))

            messages.success(request, 'Worker created successfully.')
            return redirect('accounts:workers')
        else:
            context['show_create_worker_for_VO_modal'] = True
            # prefill form with submitted data
            for field in form.fields:
                if field in form.data:
                    form.fields[field].widget.attrs['value'] = form.data[field]
            context['create_worker_for_vo_form'] = form
            return render(request, 'worker-list.html', context)


@login_required(login_url='/account/login')
def invite_user(request):
    context = {}
    context['invite_user_form'] = InviteUser()
    context['resend_token_form'] = ResendTokenForm()
    context['create_worker_for_vo_form'] = CreateWorkerForVOForm(user=request.user)

    super_user = request.user.is_superuser
    users = User.objects.all() if super_user else User.objects.filter(created_by=request.user.id)
    workers = users.filter(groups__name='worker', created_by=request.user.id)

    context['workers'] = workers
    prismic_utils = PrismicUtils(request)
    auth_common_text = prismic_utils.get_page_text('auth-common-text')
    context['auth_common_text'] = auth_common_text
    context['show_invite_modal'] = False

    form_origin = request.POST.get("form-origin", "")
    if request.method == 'POST':
        form = InviteUser(request.POST)
        if form.is_valid():
            recruited_by = None
            if request.user.groups.filter(name='taiwanese_agent').exists() or \
               request.user.groups.filter(name='indonesian_agent').exists():
                recruited_by = request.user
            user = User.objects.create_user(
                email=form.cleaned_data.get('email'),
                mobile=form.cleaned_data.get('mobile'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                is_active=False,
                access_code=get_access_code(),
                created_by=request.user.id,
                updated_by=request.user.id,
                recruited_by=recruited_by,
            )
            # Save user group/role
            group = Group.objects.get(name=form.cleaned_data.get('role'))
            user.groups.add(group)

            if form.cleaned_data.get('has_email'):
                # Send verification email with access code
                prismic_utils = PrismicUtils(request)
                auth_common_text = prismic_utils.get_page_text('auth-common-text')
                email = TunaEmailHelper()
                success = email.tuna_send_email(
                    to_emails=[user.email],
                    subject=auth_common_text.get('yourIKANAccessToken', 'Your IKAN access token'),
                    body={
                        'email': user.email,
                        'access_token': user.access_code,
                    },
                    template=EmailTemplate.ACCESS_TOKEN.value,
                    auth_common_text=auth_common_text,
                )
                if not success:
                    messages.error(request,
                                   auth_common_text.get('userCreatedErrorSendingEmail',
                                                        'User created but an error occurred while sending the email. \
                                                            Please contact support.'))
            # TODO: to be worked on with api/mobile changes
            # if form.cleaned_data.get('has_phone_number'):
            #     try:
            #         otp_service = OTPVerification()
            #         # locale = get_locale_from_request(request)
            #         # otp_service.send_otp(user.mobile, locale=locale)
            #         # add message asking user to verify their phone number and to set password using the mobile app
            #         message = auth_common_text.get('workerInviteSMSMessage', 'You have been invited to join IKAN. \
            #                                        Please download the IKAN mobile app to verify your phone number \
            #                                        and set your password. Your access code is: ') + user.access_code
            #         otp_service.send_sms(user.mobile, message)
            #     except Exception:
            #         messages.error(request,
            #                        auth_common_text.get('userCreatedErrorSendingSMS',
            #                                             'User created but an error occurred while sending the SMS. \
            #                                               Please contact support.'))

            if form_origin == 'worker-list':
                return redirect('accounts:workers')
            return redirect('accounts:users')
        else:
            context['show_invite_modal'] = True
            # prefill form with submitted data
            for field in form.fields:
                if field in form.data:
                    form.fields[field].widget.attrs['value'] = form.data[field]
            context['invite_user_form'] = form

    if form_origin == 'worker-list':
        messages.error(request, 'Error validating form!')
        return render(request, 'worker-list.html', context)
    else:
        messages.error(request, 'Error validating form!')
        return render(request, 'user-list.html', context)


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
            prismic_utils = PrismicUtils(request)
            auth_common_text = prismic_utils.get_page_text('auth-common-text')
            email = TunaEmailHelper()
            success = email.tuna_send_email(
                to_emails=[user.email],
                subject=auth_common_text.get('yourIKANAccessToken', 'Your IKAN access token'),
                body={
                    'email': user.email,
                    'access_token': user.access_code,
                },
                template=EmailTemplate.ACCESS_TOKEN.value,
                auth_common_text=auth_common_text,
            )
            if success:
                messages.success(request, 'The access code was resent successfully.')
            else:
                messages.error(request, 'An error occurred while resending the user access code.')

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
            # prefill form with submitted data
            for field in form.fields:
                if field in form.data:
                    form.fields[field].widget.attrs['value'] = form.data[field]
            context['form'] = form
            return render(request, 'register.html', context)

        user = User.objects.create_user(
            email=form.cleaned_data.get('email'),
            mobile=form.cleaned_data.get('mobile'),
            password=form.cleaned_data.get('password1'),
            first_name=form.cleaned_data.get('first_name'),
            last_name=form.cleaned_data.get('last_name'),
            is_verified=False,
            is_active=False
        )
        # Set default user group/role
        group, _ = Group.objects.get_or_create(name='public')
        user.groups.add(group)

        if form.cleaned_data.get('has_email'):
            # Send verification email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = f'{config("BASE_URL")}/api/v1/accounts/verify-email/{uid}/{token}'
            # add language query param to verification link
            verification_link += f'?language={request.session.get("language", "en-us")}'
            email_helper = TunaEmailHelper()
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject=auth_common_text.get('verifyYourEmailToStartUsingIKAN',
                                             'Verify your email to start using IKAN'),
                body={
                    'first_name': user.first_name,
                    'verification_link': verification_link,
                },
                template=EmailTemplate.VERIFY_EMAIL.value,
                auth_common_text=auth_common_text,
            )
            messages.success(request,
                             auth_common_text.get('accountCreatedCheckEmail',
                                                  'Account created successfully. \
                                                    Please check your email to verify your account.'))
            prismic_utils = PrismicUtils(request)
            success_context = {
                'reg_success_page_text': prismic_utils.get_page_text('signup-sucess'),  # Ignore typo
                }
            return render(request, template_name="register-success.html", context=success_context)

        if form.cleaned_data.get('has_phone_number'):
            messages.success(request,
                             auth_common_text.get('accountCreatedVerifyPhoneNumber',
                                                  'Account created successfully. \
                                                    Please verify your phone number to activate your account.'))
            try:
                otp_service = OTPVerification()
                locale = get_locale_from_request(request)
                send_result = otp_service.send_otp(user.mobile, locale=locale)
                if not send_result.get('success'):
                    if auth_common_text.get(send_result.get('errorKey')) is not None:
                        messages.error(request, auth_common_text.get(send_result.get('errorKey')))
                    else:
                        messages.error(request, auth_common_text.get('unableToGenerateOTP',
                                                                     'Unable to generate OTP code.'))
            except Exception:
                messages.error(request, auth_common_text.get('otpCodeSendError',
                                                             'An error occurred while sending OTP code.'))

            request.session['user_id'] = user.id
            # request.session['phone_number'] = user.mobile
            # request.session['type'] = 'mobile'
            return redirect('accounts:verify-phone-number')


class VerifyPhoneNumber(View):
    def get(self, request):
        prismic_utils = PrismicUtils(request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        user_id_from_login = request.session.get('user_id_from_login', None)
        if user_id_from_login:
            try:
                user = User.objects.get(id=user_id_from_login)
                otp_service = OTPVerification()
                locale = get_locale_from_request(request)
                send_result = otp_service.send_otp(user.mobile, locale=locale)
                if not send_result.get('success'):
                    if auth_common_text.get(send_result.get('errorKey')) is not None:
                        messages.error(request, auth_common_text.get(send_result.get('errorKey')))
                    else:
                        messages.error(request, auth_common_text.get('unableToGenerateOTP',
                                                                     'Unable to generate OTP code.'))
                request.session['user_id'] = user.id
            except Exception:
                messages.error(request, auth_common_text.get('otpCodeSendError',
                                                             'An error occurred while sending OTP code.'))

        context = {
            'auth_common_text': auth_common_text,
        }
        return render(request, template_name='verify-phone/code.html', context=context)

    def post(self, request):
        prismic_utils = PrismicUtils(request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        otp_code = request.POST.get('otp_code')
        user_id = request.session.get('user_id')
        if user_id and otp_code:
            user = User.objects.get(id=user_id)
            try:
                otp_service = OTPVerification()
                verification_resp = otp_service.check_otp(otp_code, user.mobile)
                verification_status = verification_resp.get('status')
                if verification_status == 'approved':
                    user.is_verified = True
                    user.is_mobile_verified = True
                    user.is_active = True
                    user.save()
                    messages.success(request, auth_common_text.get('phoneNumberVerifySuccess',
                                                                   'Phone number verified successfully.'))
                    return redirect('accounts:verify-phone-number-success')
                # here; other statuses
                elif verification_status == 'pending':
                    messages.error(request, auth_common_text.get('otpVerificationPending',
                                                                 'OTP verification is still pending. '
                                                                 'Please check the code and try again.'))
                elif verification_status == 'expired_or_max_attempts':
                    messages.error(request, auth_common_text.get('otpCodeExpiredApprovedOrMaxAttempts',
                                                                 'OTP verification code has expired, '
                                                                 'was already approved, OR max attempts reached. '
                                                                 'Please request a new code and try again.'))
                elif verification_status == 'blocked':
                    messages.error(request, auth_common_text.get('otpVerificationBlocked',
                                                                 'OTP verification has been blocked due to '
                                                                 'too many attempts. '
                                                                 'Please request a new code and try again.'))
                elif verification_status == 'twilio_api_error':
                    messages.error(request, auth_common_text.get('otpVerificationTwilioAPIError',
                                                                 'OTP verification failed due to a Twilio API error. '
                                                                 'Please try again later.'))
                elif verification_status == 'server_error':
                    messages.error(request, auth_common_text.get('otpVerificationServerError',
                                                                 'OTP verification failed due to a server error. '
                                                                 'Please try again later.'))
                else:
                    messages.error(request, auth_common_text.get('phoneNumberVerifyFailure',
                                                                 'Phone number verification failed. Please try again.'))
                    return redirect('accounts:verify-phone-number-failure')
            except Exception:
                messages.error(request, auth_common_text.get('otpVerificationError',
                                                             'An error occurred while verifying OTP code.'))

        messages.error(request, auth_common_text.get('missingOTPOrUserInfo',
                                                     'Missing OTP code or user information. Please try again.'))
        return render(request, template_name='verify-phone/code.html', context={'auth_common_text': auth_common_text})


def verify_phone_number_success(request):
    prismic_utils = PrismicUtils(request)
    auth_common_text = prismic_utils.get_page_text('auth-common-text')
    return render(request, template_name='verify-phone/success.html', context={'auth_common_text': auth_common_text})


def verify_phone_number_failure(request):
    prismic_utils = PrismicUtils(request)
    auth_common_text = prismic_utils.get_page_text('auth-common-text')
    return render(request, template_name='verify-phone/failure.html', context={'auth_common_text': auth_common_text})


def resend_otp(request):
    auth_common_text = PrismicUtils(request).get_page_text('auth-common-text')
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        otp_service = OTPVerification()
        locale = get_locale_from_request(request)
        send_result = otp_service.send_otp(user.mobile, locale=locale)
        if send_result.get('success'):
            messages.success(request, auth_common_text.get('otpCodeResentSuccessfully',
                                                           'OTP code resent successfully.'))
        else:
            if auth_common_text.get(send_result.get('errorKey')) is not None:
                messages.error(request, auth_common_text.get(send_result.get('errorKey')))
            else:
                messages.error(request, auth_common_text.get('unableToResendOTP', 'Unable to resend OTP code.'))
    else:
        messages.error(request, auth_common_text.get('unableToResendOTP', 'Unable to resend OTP code.'))
    return redirect('accounts:verify-phone-number')


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

        if form.cleaned_data.get('has_phone_number'):
            user = User.objects.get(mobile=form.cleaned_data.get('mobile'))
            if user:
                send_verification_code(request, user, auth_common_text)
                messages.success(request, auth_common_text.get(
                    'passwordResetOTPRequestSentMessage',
                    'Please check your phone for the OTP code to reset your password.')
                )
                return redirect('accounts:reset-password')
        if form.cleaned_data.get('has_email'):
            user = User.objects.get(email=form.cleaned_data.get('email'))
            if user:
                password_reset_token = random.randrange(111111, 999999)
                user.reset_password_token = password_reset_token
                user.save()

                email_helper = TunaEmailHelper()
                email_helper.tuna_send_email(
                    to_emails=[user.email],
                    subject=auth_common_text.get('resetYourPassword', 'Reset your IKAN password'),
                    body={
                        'first_name': user.first_name,
                        'password_reset_token': password_reset_token,
                    },
                    template=EmailTemplate.PASSWORD_RESET_REQUEST.value,
                    auth_common_text=auth_common_text,
                )
                messages.success(request, auth_common_text.get(
                    'passwordResetRequestSentMessage', 'Please check your email for the password reset code.'))
                return redirect('accounts:reset-password')
        messages.error(request,
                       auth_common_text.get('errorRequestingPasswordReset', 'Error requesting password reset.'))
        return render(request, template_name='password-reset/request-password-reset.html', context=context)


def resend_password_reset_token(request):
    prismic_utils = PrismicUtils(request)
    auth_common_text = prismic_utils.get_page_text('auth-common-text')
    email = request.session.get('reset_email', None)
    mobile = request.session.get('reset_mobile', None)
    user = None

    if mobile:
        user = User.objects.filter(mobile=mobile).first()
        if user:
            send_verification_code(request, user, auth_common_text)
            messages.success(request, auth_common_text.get(
                'passwordResetOTPRequestSentMessage',
                'Please check your phone for the OTP code to reset your password.')
            )

    if email:
        user = User.objects.filter(email=email).first()
        if user:
            password_reset_token = random.randrange(111111, 999999)
            user.reset_password_token = password_reset_token
            user.save()

            email_helper = TunaEmailHelper()
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject=auth_common_text.get('resetYourPassword', 'Reset your IKAN password'),
                body={
                    'first_name': user.first_name,
                    'password_reset_token': password_reset_token,
                },
                template=EmailTemplate.PASSWORD_RESET_REQUEST.value,
                auth_common_text=auth_common_text,
            )
            messages.success(request, auth_common_text.get(
                'passwordResetRequestSentMessage', 'Please check your email for the password reset code.'))

    if (not email and not mobile) or not user:
        messages.error(request, auth_common_text.get(
            'errorResendingPasswordResetToken', 'Error resending password reset token.'))

    return redirect('accounts:reset-password')


class ResetPassword(View):
    def get_context_data(self, **kwargs):
        context = kwargs

        prismic_utils = PrismicUtils(self.request)
        auth_common_text = prismic_utils.get_page_text('auth-common-text')
        context['auth_common_text'] = auth_common_text
        context['form'] = PasswordResetForm(auth_common_text=auth_common_text, request=self.request)
        context['show_resend_token_button'] = False
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, template_name='password-reset/reset-password.html', context=context)

    def post(self, request):
        context = self.get_context_data()
        auth_common_text = context.get('auth_common_text', {})
        form = PasswordResetForm(data=request.POST, auth_common_text=auth_common_text, request=request)
        context['form'] = form
        if not form.is_valid():
            # prefill form with submitted data
            for field in form.fields:
                if field in form.data:
                    form.fields[field].widget.attrs['value'] = form.data[field]
            context['form'] = form
            return render(request, template_name='password-reset/reset-password.html', context=context)

        if form.cleaned_data.get('has_phone_number'):
            user = User.objects.get(mobile=form.cleaned_data.get('mobile'))
            request.session['reset_mobile'] = form.cleaned_data.get('mobile')
        elif form.cleaned_data.get('has_email'):
            user = User.objects.get(email=form.cleaned_data.get('email'))
            request.session['reset_email'] = form.cleaned_data.get('email')
        else:
            user = None

        if user:
            user.set_password(form.cleaned_data.get('password1'))
            user.reset_password_token = None
            user.save()
            messages.success(request, auth_common_text.get(
                'passwordResetSuccessMessage', 'Password reset successfully. Please login with your new password.'))
            return redirect('accounts:login')
        else:
            messages.error(request, auth_common_text.get('passwordResetFailure',
                                                         'Error resetting password. Please try again.'))
            return render(request, template_name='password-reset/reset-password.html', context=context)


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


class CreateAgentVesselownerRelationshipView(LoginRequiredMixin, View):
    def post(self, request):
        form = CreateAgentVesselownerRelationshipForm(data=request.POST)
        if form.is_valid():
            agent_vo_rlshp = AgentVesselOwnerRelationship.objects.create(
                agent=form.cleaned_data['agent'],
                vessel_owner=form.cleaned_data['vessel_owner'],
                status=form.cleaned_data['status'],
                created_by=request.user.id,
                updated_by=request.user.id,
            )
            agent_vo_rlshp.save()

            messages.success(request, 'Agent/Vesselowner relationship created successfully.')
            return redirect('accounts:users')
        else:
            if form.errors.get('__all__'):
                messages.error(request, form.errors['__all__'][0])
            else:
                prismic_utils = PrismicUtils(request)
                common_text = prismic_utils.common_text
                messages.error(request, common_text.get("formIsInvalid", "Form is invalid."))
            return redirect('accounts:users')
