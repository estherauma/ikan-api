from asyncio.log import logger
from accounts.models import LoginEvent, User
from common.jwt_manager import JwtManager
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from rest_framework.views import APIView
from accounts.serializers import LoginSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny, )

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
        user = User.objects.filter(
            Q(email=email)
        ).first()
        print(email)
       
        if user and user.is_active and user.check_password(password):
            identity_manager = JwtManager()
            payload = {
                'email': user.email,
                'id': user.pk,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'isAdmin': user.is_admin,
                'roles': list(user.groups.values_list('name',flat=True))
            }
            token = identity_manager.encode(payload)
            is_first_login = user.last_login is None
            user.last_login = timezone.now()
            user.save()
            LoginEvent.objects.create(
                user=user, ip_address=request.META['REMOTE_ADDR'])
        else:
            raise AuthenticationFailed('Wrong username or password', 401)
        return Response({
            'status': 'OK',
            'data': {
                'token': token,
                'is_first_login': is_first_login
            }
        },
            status.HTTP_200_OK
        )
