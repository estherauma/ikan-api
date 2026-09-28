from accounts.models import LoginEvent, User, UserBank, UserBeneficiaries
from accounts.serializers import (
    LoginSerializer, RegisterSerializer,
    PasswordResetCheckTokenSerializer,
    PasswordResetSerializer, UserBeneficiarySerializer, UserProfileSerializer,
    UserSerializer, UserBankDetailsSerializer,
    OTPGenerateSerializer, OTPVerifySerializer
)

from accounts.sync_utils import get_sync_data, sync_push_data
from accounts.views.web import get_locale_from_request
from common.email import TunaEmailHelper, EmailTemplate
from common.jwt_manager import JwtManager
from common.twilio import TwilioService
from common.utils import get_access_code, get_user_from_get_request, get_user_from_post_request, send_email_invite
from content.utils import ContentUtils

from decouple import config

from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
# from notifications.models import Notification
from django.db.models import Q
from django.utils.dateparse import parse_datetime


import random

from companies.models import Company, UserCompany
from companies.serializers import UserCompanySerializer


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)
    throttle_scope = 'login'

    def post(self, request):
        """
            Log in a user using their email or phone number and password.

            :param request: The HTTP request object.
            :type request: HttpRequest

            :param email: The email address of the user.
            :type email: str

            :param password: The user's password.
            :type password: str

            :return: The HTTP response.
            :rtype: HttpResponse

            **Sample Request**:

                POST /login/ HTTP/1.1
                Host: example.com
                Content-Type: application/json

                {
                    "email": "user@example.com",
                    "password": "securepassword"
                }
        """
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        is_first_login = False

        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        language = data.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language

        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')

        user = None
        if email is None and phone_number is None:
            return Response({
                'status': 'FAIL',
                'message': auth_common_text.get('emailOrPhoneNumberRequired', 'Email or phone number is required')
            }, status.HTTP_400_BAD_REQUEST)
        else:
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = None
            elif phone_number:
                try:
                    user = User.objects.get(Q(telephone=phone_number) | Q(mobile=phone_number))
                    # check if the phone number is verified
                    if (user.telephone == phone_number and not user.is_telephone_verified) or\
                            (user.mobile == phone_number and not user.is_mobile_verified):
                        # TODO: DO NOT TRANSLATE, exact message is needed for client side to trigger resend otp flow
                        raise AuthenticationFailed(
                            "Your phone number is not verified. Please verify it before logging in. OR log in with email.")
                except User.DoesNotExist:
                    user = None

        if user:
            if user.is_active and user.is_verified:
                if user.check_password(password):
                    identity_manager = JwtManager()
                    if user.groups.exists():
                        payload = {
                            'email': user.email if user.email else '',
                            'mobile': user.mobile if user.mobile else '',
                            'id': user.pk,
                            'firstName': user.first_name,
                            'lastName': user.last_name,
                            'role': list(user.groups.values_list('name', flat=True))[0],
                            'roles': list(user.groups.values_list('name', flat=True)) if user.groups.exists() else [],
                        }
                        token = identity_manager.encode(payload)
                        is_first_login = user.last_login is None
                        user.last_login = timezone.now()
                        user.save()
                        LoginEvent.objects.create(
                            user=user, ip_address=request.META['REMOTE_ADDR'])
                    else:
                        raise AuthenticationFailed(
                            auth_common_text.get('authFailedContactAdmin', 'Authentication failed, contact admin'), 401)
                else:
                    raise AuthenticationFailed(
                        auth_common_text.get('invalidPasswordTryAgain', 'Invalid password, please try again'), 401)
            else:
                if user.is_verified is False:
                    raise AuthenticationFailed(
                        auth_common_text.get('verifyAccountToContinue', 'Verify your account to continue.'), 401)
                raise AuthenticationFailed(
                    auth_common_text.get('accountNotActivated', 'Account is not activated, contact admin'), 401)
        else:
            raise AuthenticationFailed(auth_common_text.get('userDoesNotExist', 'User does not exist'), 401)
        return Response({
            'status': 'OK',
            'data': {
                'token': token,
                'is_first_login': is_first_login,
                'user_data': payload,
                'sync_data': get_sync_data(user),
            }
        },
            status.HTTP_200_OK
        )


class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request):
        '''Register a user
        Args:
            request(Request): HTTP request
        '''
        data = request.data
        language = data.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language

        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')

        if not data.get('email') and not data.get('phone_number'):
            return Response({
                'status': 'FAIL',
                'message': auth_common_text.get('emailOrPhoneNumberRequired',
                                                'Either email or phone number is required.')
            }, status.HTTP_400_BAD_REQUEST)
        if data.get('phone_number'):
            data['mobile'] = data['phone_number']

        serializer = self.serializer_class(data=data, auth_common_text=auth_common_text)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False)

        # Set default user group/role
        role = data.get('role', data.get('user_role', 'public'))
        group = Group.objects.get(name=role) if \
            Group.objects.filter(name=role).exists() else Group.objects.get_or_create(name='public')[0]
        user.groups.add(group)

        if data.get('email'):
            # Send verification email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_link = f'{config("BASE_URL")}/api/v1/accounts/verify-email/{uid}/{token}'
            # add language query param to verification link
            verification_link += f'?language={language}'
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
        # Code block commented out as the otp code generation is triggered from the frontend after account creation.
        # if data.get('phone_number'):
        #     # Send verification otp code to phone number
        #     try:
        #         otp_service = TwilioService()
        #         locale = get_locale_from_request(request)
        #         otp_service.send_otp(user.mobile, locale=locale)
        #     except Exception:
        #         pass

        return Response(
            {
                'status': 'OK',
                # 'message': 'Account created successfully. Please check your email to verify your account.'
                'message': 'Account created successfully. Please verify your account.'
            },
            status.HTTP_201_CREATED
        )


def verify_email(request, uidb64, token):
    try:
        # Set language from query param
        language = request.GET.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language

        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.is_active = True
            user.save()
            # notify_admin(user) ## Disabled as new users are automatically actived above, no need for admin activation
            return redirect('accounts-api:verify-email-success')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass
    return redirect('accounts-api:verify-email-failure')


def notify_admin(user):
    message = f"A new user {user.email} has registered and needs activation."
    email_helper = TunaEmailHelper()
    email_helper.tuna_send_email(
        to_emails=[config('ADMIN_EMAIL')],
        subject='IKAN: New user registration',
        body=message,
    )


def verify_email_success(request):
    content_utils = ContentUtils(request)
    auth_common_text = content_utils.get_page_text('auth-common-text')
    return render(request, template_name='verify-email/success.html', context={'auth_common_text': auth_common_text})


def verify_email_failure(request):
    content_utils = ContentUtils(request)
    auth_common_text = content_utils.get_page_text('auth-common-text')
    return render(request, template_name='verify-email/failure.html', context={'auth_common_text': auth_common_text})


class RequestPasswordReset(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        language = request.data.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language
        if not email and not phone_number:
            return Response({
                'status': 'FAIL',
                'message': 'Email or phone number is required',
            }, status.HTTP_400_BAD_REQUEST)

        user_queryset = User.objects.none()
        if email:
            user_queryset = User.objects.filter(email=email)
        if phone_number:
            user_queryset = User.objects.filter(Q(mobile=phone_number) | Q(telephone=phone_number))
        user = user_queryset.first()
        if user and email:
            password_reset_token = random.randrange(111111, 999999)
            user.reset_password_token = password_reset_token
            user.save()

            content_utils = ContentUtils(request)
            auth_common_text = content_utils.get_page_text('auth-common-text')
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
            return Response(
                {
                    'status': 'OK',
                    'message': 'Password reset request was successful. \
                        Please check your email for the password reset code.'
                },
                status.HTTP_200_OK
            )
        elif user and phone_number:
            try:
                otp_service = TwilioService()
                locale = get_locale_from_request(request)
                otp_service.send_otp(user.mobile, locale=locale)
                return Response(
                    {
                        'status': 'OK',
                        'message': 'Password reset request was successful. \
                            Please check your phone for the password reset code.'
                    },
                    status.HTTP_200_OK
                )
            except Exception:
                pass

        return Response(
            {
                'status': 'FAIL',
                'message': 'Password reset request was unsuccessful.'
            },
            status.HTTP_400_BAD_REQUEST
        )


class PasswordResetCheckToken(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            data = request.data

            language = data.get('language', 'en-us')
            supported_languages = ['en-us', 'id-id', 'qm-zh']
            if language not in supported_languages:
                language = 'en-us'
            request.session['language'] = language

            content_utils = ContentUtils(request)
            auth_common_text = content_utils.get_page_text('auth-common-text')
            serializer = PasswordResetCheckTokenSerializer(
                data=data, auth_common_text=auth_common_text, context={'request': request})
            serializer.is_valid(raise_exception=True)

            return Response(
                {
                    'status': 'OK',
                    'message': 'Password reset token confirmed'
                },
                status.HTTP_200_OK
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return Response(
            {
                'status': 'ERROR',
                'message': 'Password reset failed.'
            },
            status.HTTP_400_BAD_REQUEST
        )


class ResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            data = request.data

            language = data.get('language', 'en-us')
            supported_languages = ['en-us', 'id-id', 'qm-zh']
            if language not in supported_languages:
                language = 'en-us'
            request.session['language'] = language

            content_utils = ContentUtils(request)
            auth_common_text = content_utils.get_page_text('auth-common-text')

            serializer = PasswordResetSerializer(data=data, auth_common_text=auth_common_text)
            serializer.is_valid(raise_exception=True)

            email = request.data.get('email')
            phone_number = request.data.get('phone_number')
            password = request.data.get('password')
            user_queryset = User.objects.none()
            if email:
                user_queryset = User.objects.filter(email=email)
            if phone_number:
                user_queryset = User.objects.filter(Q(mobile=phone_number) | Q(telephone=phone_number))
            user = user_queryset.first()
            if user:
                user.set_password(password)
                user.reset_password_token = None
                user.save()
                return Response(
                    {
                        'status': 'OK',
                        'message': 'Password reset successful.'
                    },
                    status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'ERROR',
                        'message': auth_common_text.get('userDoesNotExist', 'User does not exist')
                    },
                    status.HTTP_400_BAD_REQUEST
                )

        except (TypeError, ValueError, OverflowError):
            pass
        return Response(
            {
                'status': 'ERROR',
                'message': auth_common_text.get('passwordResetFailure', 'Password reset failed.'),
            },
            status.HTTP_400_BAD_REQUEST
        )


class VerifyAndSetPassword(APIView):
    def post(self, request):
        '''Verify a user and set password
        Args:
            request(Request): HTTP request
        '''
        data = request.data

        language = data.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language

        access_code = data.get('access_code')
        '''
            access code field on the db can be blank or null.
            So we need to check for None so we don't get back all records for users
            who have already verified and set their passwords
        '''
        if access_code is None:
            return Response(
                {
                    'status': 'Failed',
                    'message': 'Access code is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(access_code=access_code)
            user.is_verified = True
            user.is_active = True
            if data.get('password') == data.get('password_confirm'):
                user.set_password(data.get('password'))
                user.access_code = None
                user.save()
                # notify_admin(user) ## Disabled as new users are automatically actived above, \
                # no need for admin activation
                return Response(
                    {
                        'status': 'OK',
                        'message': 'Account verified and password set successfully.'
                    },
                    status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'ERROR',
                        'message': 'Passwords do not match.'
                    },
                    status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Invalid access code.'
                },
                status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(APIView):
    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        user = self.get_user(pk)
        serializer = UserSerializer(user)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        })

    def delete(self, request, pk):
        user = self.get_user(pk)
        user.delete()
        return Response({
            'status': 'OK',
            'message': 'User deleted successfully',
            'data': [],
            'errors': []
        }, status=status.HTTP_204_NO_CONTENT)


class InviteUser(APIView):
    def post(self, request):
        '''Invite a user
        Args:
            request(Request): HTTP request
        '''
        data = request.data

        language = data.get('language', 'en-us')
        supported_languages = ['en-us', 'id-id', 'qm-zh']
        if language not in supported_languages:
            language = 'en-us'
        request.session['language'] = language

        email = data.get('email')
        mobile = data.get('mobile', data.get('phone_number'))
        role = data.get('role')
        if email is None and mobile is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Either email or phone number is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        if role is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Role is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        user_queryset = User.objects.none()
        if email:
            user_queryset = User.objects.filter(email=email)
        if mobile:
            user_queryset = User.objects.filter(Q(mobile=mobile) | Q(telephone=mobile))
        user_exists = user_queryset.exists()
        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')
        if not user_exists:
            serializer = RegisterSerializer(data=data, auth_common_text=auth_common_text)
            serializer.is_valid(raise_exception=True)
            user = User.objects.create_user(
                email=email,
                mobile=mobile,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                access_code=get_access_code(),
                is_verified=False,
                is_active=False,
            )

            group = Group.objects.get(name=data.get('role'))
            user.groups.add(group)

            return send_email_invite(user, auth_common_text=auth_common_text)
        else:
            user = user_queryset.first()

            if user.email is not None and not user.is_verified and not user.is_active:
                return send_email_invite(user, auth_common_text=auth_common_text)
            # if user.mobile is not None and ((user.mobile == mobile and not user.is_mobile_verified) or
            #                                 (user.telephone == mobile and not user.is_mobile_verified)):
            #     # TODO: check is this logic is required
            #     pass
            else:
                return Response(
                    {
                        'status': 'OK',
                        'message': 'User already invited.'
                    },
                    status.HTTP_200_OK
                )


class UserListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        role = request.GET.get('role')
        if role is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Role is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        try:
            Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Invalid role.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        users = User.objects.filter(groups__name=role, created_by=request.user.id)
        serializer = UserProfileSerializer(users, many=True)

        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        })


class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        # if request has a query param of user id, then get that user instead
        user_id = request.GET.get('user_id')
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
        serializer = UserProfileSerializer(user)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        try:
            # register new user profile
            if request.query_params.get('register') == 'register':
                user = None
                try:
                    if request.data['email']:
                        user = User.objects.get(email=request.data['email'])
                    if request.data['mobile']:
                        user = User.objects.get(mobile=request.data['mobile'])
                except User.DoesNotExist:
                    user = None

                if user:
                    user_id = user.id
                else:
                    if request.data['user_role'] is None:
                        return Response(
                            {
                                'status': 'FAIL',
                                'message': 'Role is required.'
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        new_user = User.objects.create_user(
                            email=request.data['email'],
                            mobile=request.data['mobile'],
                            first_name=request.data['first_name'],
                            last_name=request.data['last_name'],
                            access_code=get_access_code(),
                            is_verified=False,
                            is_active=False,
                        )
                        role = request.data['user_role']
                        group = Group.objects.get(name=role)
                        new_user.groups.add(group)

                        user_id = new_user.id
            elif request.data['user_id'] is not None:
                try:
                    user = User.objects.get(pk=request.data['user_id'], email=request.data['email'])
                    user_id = user.id
                except User.DoesNotExist:
                    return Response(
                        {
                            'status': 'FAIL',
                            'message': 'User not found.'
                        },
                        status.HTTP_404_NOT_FOUND
                    )
        except KeyError:
            user_id = request.user.id

        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
        data = request.data
        serializer = UserProfileSerializer(user, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)


class UpdateUserCompany(APIView):
    """
    API endpoint for updating user-company relationships.

    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get user companies.

        If a 'user_id' query parameter is provided, retrieve companies for that user.
        If the user is not found, return a 404 response.

        Returns a list of user companies along with their details.
        """
        user = request.user.id
        # if request has a query param of user id, then get that user instead
        user_id = request.GET.get('user_id')
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
        # get user companies
        user_companies = UserCompany.objects.filter(user=user)
        serializer = UserCompanySerializer(user_companies, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create or update a user-company relationship.

        Requires 'user_id', 'company_id', 'role', 'start_date', and 'end_date' in the request data.
        Check if the user and company exist, return a 404 response if not.
        Check if the user is already linked to the company, return a 400 response if true.
        If the user is linked to other companies, mark them as inactive.

        Returns the details of the created or updated user-company relationship.
        """
        user_id = request.data['user_id']
        company_id = request.data['company_id']

        # check if user exists and return if not
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        # check if company exists and return if not
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Company not found.'
                },
                status.HTTP_404_NOT_FOUND
            )

        # check if user is already linked to company and if they are return
        user_company_exists = UserCompany.objects.filter(user=user, company=company).exists()
        if user_company_exists:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User already linked to company.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        # if not linked, check other company linkages and mark them as inactive
        user_company = None
        try:
            user_company = UserCompany.objects.get(user=user, is_active=True)
        except UserCompany.DoesNotExist:
            user_company = None
        if user_company:
            user_company.is_active = False
            user_company.save()

        # add entry to Usercompany
        user_company = UserCompany.objects.create(
            user=user,
            company=company,
            role=request.data['role'],
            start_date=request.data['start_date'],
            end_date=request.data['end_date'],
        )
        user_company.save()
        serializer = UserCompanySerializer(user_company)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)


class UserBankDetailsApiView(APIView):
    """
    Manage user bank account details
    Requires authentication
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get user banks.
        If a `user_id` param is passed, retrive the companies for that user.
        If not, it'll return companies of that user
        """
        user = get_user_from_get_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            user_banks = UserBank.objects.filter(user=user)
            serializer = UserBankDetailsSerializer(user_banks, many=True)
            return Response({
                'status': 'OK',
                'data': serializer.data,
                'errors': []
            }, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_post_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            serializer_data = {**request.data, 'user': user}
            serializer = UserBankDetailsSerializer(data=serializer_data)

            if serializer.is_valid():
                # check if user already has account details and mark them as inactive
                user_bank = None
                try:
                    user_bank = UserBank.objects.get(user=user, is_active=True)
                except UserBank.DoesNotExist:
                    user_bank = None
                if user_bank:
                    user_bank.is_active = False
                    user_bank.save()
                # check if user has account with the same account name and number
                similar_bank_exists = UserBank.objects.filter(
                    user=user, account_name=request.data['account_name'],
                    account_number=request.data['account_number']).exists()

                if similar_bank_exists:
                    return Response({
                        'status': 'FAIL',
                        'message': 'User bank account exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response({
                    'status': 'OK',
                    'data': serializer.data,
                    'errors': []
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'FAIL',
                    'data': [],
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            user_bank = UserBank.objects.get(pk=pk)
        except UserBank.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User bank not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > user_bank.updated_at:
            serializer = UserBankDetailsSerializer(user_bank, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': UserBankDetailsSerializer(user_bank).data
            }, status=status.HTTP_200_OK)


class UserBeneficiariesApiView(APIView):
    """
    Manage user beneficiaries
    Requires authentication
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = get_user_from_get_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            user_beneficiaries = UserBeneficiaries.objects.filter(user=user)
            serializer = UserBeneficiarySerializer(user_beneficiaries, many=True)
            return Response({
                'status': 'OK',
                'data': serializer.data,
                'errors': []
            }, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_post_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            serializer_data = {**request.data, 'user': user}
            serializer = UserBeneficiarySerializer(data=serializer_data)
            if serializer.is_valid():
                # check if user has beneficiary with the same account number
                beneficiary_exists = UserBeneficiaries.objects.filter(
                    user=user, account_number=request.data['account_number']).exists()
                if beneficiary_exists:
                    return Response(
                        {
                            'status': 'FAIL',
                            'message': 'Beneficiary with the same account number already exists.'
                        },
                        status.HTTP_400_BAD_REQUEST
                    )
                else:
                    serializer.save()
                    return Response({
                        'status': 'OK',
                        'data': serializer.data,
                        'errors': []
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'FAIL',
                    'data': [],
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            beneficiary = UserBeneficiaries.objects.get(pk=pk)
        except UserBeneficiaries.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Beneficiary not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > beneficiary.updated_at:
            serializer = UserBeneficiarySerializer(beneficiary, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status.HTTP_200_OK)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes were made.',
                'data': UserBeneficiarySerializer(beneficiary).data
            }, status.HTTP_200_OK)


class GetOTP(APIView):
    def post(self, request, *args, **kwargs):
        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')
        serializer = OTPGenerateSerializer(data=request.data, auth_common_text=auth_common_text)

        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id', None)
            try:
                if user_id:
                    user = User.objects.get(id=user_id)
                else:
                    number = serializer.validated_data['phone_number']
                    user = User.objects.get(Q(mobile=number) | Q(telephone=number))
            except User.DoesNotExist:
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('userDoesNotExist', 'User does not exist.'),
                    "errorKey": "userDoesNotExist"
                    }, status=status.HTTP_400_BAD_REQUEST)

            resp = serializer.start_otp_process()
            if resp.get('status') == 'pending':
                num_type = request.data.get('type', None)
                if num_type is None or num_type == 'mobile':
                    user.mobile = serializer.validated_data['phone_number']
                elif num_type == 'telephone':
                    user.telephone = serializer.validated_data['phone_number']
                user.save()
                return Response({"status": resp.get('status')}, status=status.HTTP_200_OK)
            elif resp.get('status') == 'invalid_number':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationInvalidNumber',
                                                  'Invalid phone number provided. '
                                                  'Please check the number and try again.'),
                    "errorKey": "otpCodeGenerationInvalidNumber"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif resp.get('status') == 'invalid_country_code':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationInvalidCountryCode',
                                                  'The provided phone number has an invalid country code.'),
                    "errorKey": "otpCodeGenerationInvalidCountryCode"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif resp.get('status') == 'too_many_requests':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationTooManyRequests',
                                                  'Too many OTP requests have been made for this number. '
                                                  'Please wait and try again later.'),
                    "errorKey": "otpCodeGenerationTooManyRequests"
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif resp.get('status') == 'sms_not_supported':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationSMSNotSupported',
                                                  'The provided phone number does not support receiving SMS messages.'),
                    "errorKey": "otpCodeGenerationSMSNotSupported"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif resp.get('status') == 'blocked':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationBlocked',
                                                  'OTP code generation has been blocked due to too many attempts. '
                                                  'Please request a new code and try again.'),
                    "errorKey": "otpCodeGenerationBlocked"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif resp.get('status') == 'twilio_api_error':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationTwilioAPIError',
                                                  'OTP code generation failed due to a Twilio API error. '
                                                  'Please try again later.'),
                    "errorKey": "otpCodeGenerationTwilioAPIError"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif resp.get('status') == 'server_error':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationServerError',
                                                  'OTP code generation failed due to a server error. '
                                                  'Please try again later.'),
                    "errorKey": "otpCodeGenerationServerError"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeGenerationFailed',
                                                  'OTP code generation failed. Please try again.'),
                    "errorKey": "otpCodeGenerationFailed"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class VerifyOTP(APIView):
    def post(self, request, *args, **kwargs):
        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')
        serializer = OTPVerifySerializer(data=request.data, auth_common_text=auth_common_text)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id', None)
            try:
                if user_id:
                    user = User.objects.get(id=user_id)
                else:
                    number = serializer.validated_data['phone_number']
                    user = User.objects.get(Q(mobile=number) | Q(telephone=number))
            except User.DoesNotExist:
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('userDoesNotExist', 'User does not exist.'),
                    "errorKey": "userDoesNotExist"
                    }, status=status.HTTP_400_BAD_REQUEST)

            result = serializer.verify_otp()
            if result.get('status') == 'approved':
                num_type = serializer.validated_data.get('type', None)
                if num_type == "mobile" or num_type is None:
                    user.is_mobile_verified = True
                    # message = 'Your mobile phone number has been verified successfully.'
                elif num_type == "telephone":
                    user.is_telephone_verified = True
                    # message = 'Your telephone number has been verified successfully.'
                user.is_verified = True
                user.is_active = True
                user.save()
                # TODO: Create notification
                # Notification.objects.create(
                #     user=user,
                #     title='Verification success',
                #     message=message,
                #     status='unread'
                # )
                return Response({"status": result.get('status')}, status=status.HTTP_200_OK)
            elif result.get('status') == 'pending':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpVerificationPending',
                                                  'OTP verification is still pending. '
                                                  'Please check the code and try again.'),
                    "errorKey": "otpVerificationPending"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif result.get('status') == 'expired_or_max_attempts':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpCodeExpiredApprovedOrMaxAttempts',
                                                  'OTP verification code has expired, was already approved,'
                                                  ' OR max attempts reached. Please request a new code and try again.'),
                    "errorKey": "otpCodeExpiredApprovedOrMaxAttempts"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif result.get('status') == 'blocked':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpVerificationBlocked',
                                                  'OTP verification has been blocked due to too many attempts. '
                                                  'Please request a new code and try again.'),
                    "errorKey": "otpVerificationBlocked"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif result.get('status') == 'twilio_api_error':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpVerificationTwilioAPIError',
                                                  'OTP verification failed due to a Twilio API error. '
                                                  'Please try again later.'),
                    "errorKey": "otpVerificationTwilioAPIError"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif result.get('status') == 'server_error':
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpVerificationServerError',
                                                  'OTP verification failed due to a server error. '
                                                  'Please try again later.'),
                    "errorKey": "otpVerificationServerError"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    "status": 'error',
                    "error": auth_common_text.get('otpVerificationFailed',
                                                  'OTP verification failed. Please check the code and try again.'),
                    "errorKey": "otpVerificationFailed"
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class CheckPhoneNumberUniquenessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Check if a phone number is already used by another user.
        Allows the same user to reuse a number for both mobile & telephone.
        Trims whitespace before checking.
        """
        content_utils = ContentUtils(request)
        auth_common_text = content_utils.get_page_text('auth-common-text')

        phone_number = request.data.get("phone_number")
        user_id = request.data.get("user_id", None)

        if not phone_number:
            return Response(
                {"detail": auth_common_text.get('phoneNumberRequired', 'Phone number is required.')},
                status=400
            )
        # commenting out user_id required check to allow for new users
        # if not user_id:
        #     return Response({"detail": auth_common_text.get('userIDRequired', 'User ID is required.')}, status=400)

        phone_number = phone_number.strip()

        exists = User.objects.filter(
            Q(mobile=phone_number) | Q(telephone=phone_number)
        ).exclude(pk=user_id).exists()

        return Response({
            "unique": not exists,
            "phone_number": phone_number
        }, status.HTTP_200_OK)


class SyncUserData(APIView):
    """
    API endpoint for syncing user data.
    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'sync'

    def get(self, request):
        """
        Sync user data.

        Returns the user's data (to be synced to the mobile app) based on their role and permissions.
        An optional `lastSyncedAt` query param restricts the response to records changed since then.
        """
        user = request.user
        profile = UserProfileSerializer(user).data
        last_synced_at = parse_datetime(request.query_params.get('lastSyncedAt') or '')

        return Response({
            'status': 'OK',
            'data': {
                'user_data': profile,
                'sync_data': get_sync_data(user, last_synced_at),
            }
        })

    def post(self, request):
        """
        Push records created/updated on the mobile app while offline, to be synced to the server.
        """
        result = sync_push_data(request.user, request.data)

        return Response({
            'status': 'OK',
            'data': {
                'survey_synced': result['survey_synced'],
                'errors': result['errors'],
            }
        })
