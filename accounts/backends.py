from rest_framework import authentication, exceptions
from accounts.models import User
from common.jwt_manager import JwtManager
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.core.exceptions import ValidationError


class JWTAuthentication(authentication.BaseAuthentication):
    '''JWT Authentication backend for the api endpoints'''

    def authenticate(self, request):
        token = authentication.get_authorization_header(
            request).decode('utf-8')
        if not token:
            return None
        try:
            if 'Bearer ' not in token:
                raise exceptions.AuthenticationFailed(
                    "Bad request. The token should begin with the word 'Bearer'."
                )
            token = token.split(' ')[1]
            identity_manager = JwtManager()
            payload = identity_manager.decode(token)
        except IndexError:
            raise exceptions.AuthenticationFailed(
                "Bad request, missing token after 'Bearer' ", 400)
        try:
            user = User.objects.get(pk=payload['id'], is_active=True)
        except User.DoesNotExist:
            raise exceptions.NotAuthenticated('User not authenticated', 401)
        return user, token


class EmailOrPhoneNumberBackend(ModelBackend):
    def authenticate(self, request, email_or_phone=None, password=None, **kwargs):
        user = None

        if email_or_phone:
            try:
                if '@' in email_or_phone:
                    user = User.objects.get(email=email_or_phone)
                else:
                    user = User.objects.get(
                        Q(telephone=email_or_phone) | Q(mobile=email_or_phone)
                    )
                    # Phone number should be verified
                    if (user.telephone == email_or_phone and not user.is_telephone_verified) or\
                            (user.mobile == email_or_phone and not user.is_mobile_verified):
                        raise ValidationError("Your phone number is not verified. Please verify it before logging in. OR log in with email")
            except User.DoesNotExist:
                return None
            except ValidationError as e:
                if request is not None:
                    request.unverified_number_err = str(e)
                return None

            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
