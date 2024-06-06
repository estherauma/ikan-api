import os
from django.http import HttpResponse
from decouple import config
from rest_framework.response import Response
from rest_framework.decorators import api_view
import django
from django.db.utils import OperationalError
from tuna.serializers import UploadFileSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.models import User

enviroment = config('ENVIRONMENT', 'Development')


def welcome(request):
    return HttpResponse(f"Welcome to the Tuna {enviroment} API")


@api_view(['GET'])
def health(request):
    heath_params = {"app server": "active"}
    try:
        django.db.connection.ensure_connection()
        heath_params["database"] = "active"
    except OperationalError:
        heath_params["database"] = "down"

    return Response(heath_params)


# Function is used with test to ensure that camelCasel renderer and snake_case parser are configured  well
# If not, the tests should fail and give you an indication of what's failed. Otherwise the client apps will fail
@api_view(('GET', 'POST'))
def sample_data(request):
    if request.method == 'GET':
        return Response({
            'name': 'test',
            'test_data': 'test_data'
        })
    if request.method == 'POST':
        if request.data['parser_works']:
            return Response({
                'status': 'OK'
            })
        else:
            return Response({
                'status': 'FAILED'
            })


class UploadFileView(APIView):
    permission_classes = ([IsAuthenticated, ])
    upload_paths = {
        'contract': 'uploads/contracts',
        'passport': 'uploads/passports',
        'profile_picture': 'uploads/profiles',
        'vessel_image': 'uploads/vessel_images'
    }

    def post(self, request):
        file_serializer = UploadFileSerializer(data=request.data)
        if file_serializer.is_valid():
            # based on entitytype, create upload path if not exists
            upload_path = self.upload_paths.get(request.data['entity_type'])
            if upload_path:
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
            else:
                return Response({'error': 'Invalid entity type'}, status=status.HTTP_400_BAD_REQUEST)

            if request.data['user_id']:
                user_id = request.data['user_id']
                user = User.objects.get(pk=user_id)
            else:
                user_id = request.user.id
                user = request.user

            # write the file to the right path
            # the _ikan_ prefix is used in the mobile app to get the file name
            file_path = self.upload_paths[request.data['entity_type']] + '/' + str(user_id) + '_ikan_' +\
                file_serializer.validated_data['file_content'].name
            # get extension from file name
            file_extension = os.path.splitext(file_path)[1]
            with open(file_path, 'wb+') as destination:
                for chunk in file_serializer.validated_data['file_content'].chunks():
                    destination.write(chunk)

            # save the file path in the user profile
            if request.data['entity_type'] == 'profile_picture':
                user.profile_image = file_path
                user.save()
            return Response({
                'status': 'OK',
                'data': {
                    'file_location': file_path,
                    'file_type': file_extension
                }
            }, status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
