import datetime
import jwt
from django.conf import settings
from rest_framework import exceptions

from common.logger import logger

INVALID_TOKEN_MSG = "Authorization failed due to an Invalid token.",
EXPIRED_TOKEN_MSG = "Token expired. Please login to get a new token",
SIGNATURE_ERROR = "Cannot verify the signature of the token provided asit was signed by a non matching private key",
SERVER_ERROR_MESSAGE = "Authorization failed. Please contact support.",
NO_BEARER_MSG = "Bad request. The token should begin with the word 'Bearer'.",
NO_TOKEN_MSG = "Bad request. Header does not contain an authorization token."


EXCEPTION_MAPPER = {
    ValueError: (SERVER_ERROR_MESSAGE, 500),
    TypeError: (SERVER_ERROR_MESSAGE, 500),
    jwt.ExpiredSignatureError: (EXPIRED_TOKEN_MSG, 401),
    jwt.DecodeError: (INVALID_TOKEN_MSG, 401),
    jwt.InvalidSignatureError: (SIGNATURE_ERROR, 500)
}


class JwtManager():
    ''' User identity management creates a token'''

    def decode(self, token):
        '''Decode token
        Args:
            token (string): Bearer token
         '''

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=['HS256'], options={
                    'verify_signature': True,
                    'verify_exp': True
                })
        except (
            ValueError,
            TypeError,
            jwt.ExpiredSignatureError,
            jwt.DecodeError,
            jwt.InvalidSignatureError
        ) as error:
            message, status_code = EXCEPTION_MAPPER.get(
                type(error), (SERVER_ERROR_MESSAGE, 500))
            logger.error('%s: %s', message, status_code)
            raise exceptions.AuthenticationFailed(
                detail={'message': message}, code=status_code) from error
        except Exception as e:
            raise exceptions.APIException(detail=e.__str__(), code=500) from e
        else:
            return payload

    def encode(self, data):
        ''' Encode data
        Args:
            data (dict): Payload to encode
            exp (int): Expires in seconds
        '''
        data.update({'iss': settings.TOKEN_ISSUER,
                     'iat': datetime.datetime.utcnow(),
                     'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.TOKEN_EXPIRATION_TIME)})
        encoded = jwt.encode(data, settings.SECRET_KEY, algorithm='HS256')
        return encoded
