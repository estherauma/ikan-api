from django.shortcuts import redirect, render
from accounts.models import LoginEvent, User
from common.email import TunaEmailHelper, EmailTemplate
from common.jwt_manager import JwtManager
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from django.utils import timezone
from rest_framework.views import APIView
from accounts.serializers import LoginSerializer, RegisterSerializer
from rest_framework.response import Response
from rest_framework import status
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        '''Login a user
        Args:
            request(Request): HTTP request
        '''
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
            subject='Verify your email to start using Ikan',
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
            notify_admin(user)
            return redirect('verify-email-success')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass
    return redirect('verify-email-failure')


def notify_admin(user):
    message = f"A new user {user.email} has registered and needs activation."
    email_helper = TunaEmailHelper()
    email_helper.tuna_send_email(
        to_emails=[config('ADMIN_EMAIL')],
        subject='Ikan: New user registration',
        body=message,
    )


def verify_email_success(request):
    return render(request, template_name='verify-email/success.html')


def verify_email_failure(request):
    return render(request, template_name='verify-email/failure.html')
