from django.shortcuts import redirect, render
from accounts.models import LoginEvent, User
from common.email import TunaEmailHelper, EmailTemplate
from common.jwt_manager import JwtManager
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from django.utils import timezone
from rest_framework.views import APIView
from accounts.serializers import LoginSerializer, RegisterSerializer, \
    PasswordResetCheckTokenSerializer, PasswordResetSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import random


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """
            Log in a user using their email and password.

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
        password = data.get('password')
        user = User.objects.filter(email=email).first()
        if user:
            if user.is_active:
                if user.check_password(password):
                    identity_manager = JwtManager()
                    if user.groups.exists():
                        payload = {
                            'email': user.email,
                            'id': user.pk,
                            'firstName': user.first_name,
                            'lastName': user.last_name,
                            'isAdmin': user.is_admin,
                            'role': list(user.groups.values_list('name', flat=True))[0]
                        }
                        token = identity_manager.encode(payload)
                        is_first_login = user.last_login is None
                        user.last_login = timezone.now()
                        user.save()
                        LoginEvent.objects.create(
                            user=user, ip_address=request.META['REMOTE_ADDR'])
                    else:
                        raise AuthenticationFailed('Authentication failed, contact admin', 401)
                else:
                    raise AuthenticationFailed('Invalid password, please try again', 401)
            else:
                raise AuthenticationFailed('User account is not activated, contact admin', 401)
        else:
            raise AuthenticationFailed('User does not exist', 401)
        return Response({
            'status': 'OK',
            'data': {
                'token': token,
                'is_first_login': is_first_login,
                'user_data': payload,
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
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False)

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

        return Response(
            {
                'status': 'OK',
                'message': 'Account created successfully. Please check your email to verify your account.'
            },
            status.HTTP_201_CREATED
        )


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            notify_admin(user)
            return redirect('verify-email-success')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass
    return redirect('verify-email-failure')


def notify_admin(user):
    message = f"A new user {user.email} has registered and needs activation."
    admin_email = config('ADMIN_EMAIL')
    email_helper = TunaEmailHelper()
    email_helper.tuna_send_email(
        to_emails=[config('ADMIN_EMAIL')],
        subject='IKAN: New user registration',
        body=message,
    )


def verify_email_success(request):
    return render(request, template_name='verify-email/success.html')


def verify_email_failure(request):
    return render(request, template_name='verify-email/failure.html')


class RequestPasswordReset(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'status': 'FAIL',
                'message': 'Email is required',
            }, status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
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

        return Response(
            {
                'status': 'OK',
                'message': 'Password reset request was successful. Please check your email for the password reset code.'
            },
            status.HTTP_200_OK
        )


class PasswordResetCheckToken(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            data = request.data
            serializer = PasswordResetCheckTokenSerializer(data=data)
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
            serializer = PasswordResetSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            email = request.data.get('email')
            password = request.data.get('password')
            user = User.objects.filter(email=email).first()
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
                        'error': 'User does not exist'
                    },
                    status.HTTP_400_BAD_REQUEST
                )

        except (TypeError, ValueError, OverflowError):
            pass
        return Response(
            {
                'status': 'ERROR',
                'message': 'Password reset failed.',
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
                notify_admin(user)
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
