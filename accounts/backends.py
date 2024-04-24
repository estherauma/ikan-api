from rest_framework import authentication, exceptions

from accounts.models import User
from common.jwt_manager import JwtManager


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
        except IndexError as e:
            raise exceptions.AuthenticationFailed(
                "Bad request, missing token after 'Bearer' ", 400)
        try:
            user = User.objects.get(pk=payload['id'], is_active=True)
        except User.DoesNotExist:
            raise exceptions.NotAuthenticated('User not authenticated', 401)
        return user, token
