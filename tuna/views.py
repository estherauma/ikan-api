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
from vessels.models import Vessel, VesselImage
from contracts.models import Contract, ContractDocument
from django.forms.models import model_to_dict

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

            if request.data.get('user_id') is not None:
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

            if request.data['entity_type'] == 'profile_picture':
                user.profile_image = file_path
                user.save()
                result_obj = None
            elif request.data['entity_type'] == 'vessel_image':
                vessel_id = request.data.get('vessel_id')
                vessel = Vessel.objects.get(pk=vessel_id)
                if VesselImage.objects.filter(vessel=vessel).exists():
                    vessel_image = VesselImage.objects.get(vessel=vessel)
                    vessel_image.image_url = file_path
                    vessel_image.description = request.data.get('description')
                    vessel_image.updated_by = request.data.get('updated_by', user_id)
                    vessel_image.updated_at = request.data.get('updated_at')
                    vessel_image.save()
                else:
                    vessel_image = VesselImage.objects.create(
                        app_ref=request.data.get('app_ref'),
                        vessel=vessel,
                        image_url=file_path,
                        description=request.data.get('description'),
                        created_by=request.data.get('created_by', user_id),
                        updated_by=request.data.get('updated_by', user_id),
                        created_at=request.data.get('created_at'),
                        updated_at=request.data.get('updated_at'),
                    )
                    vessel_image.save()
                result_obj = {'vessel_image': model_to_dict(vessel_image)}
            elif request.data['entity_type'] == 'contract':
                contract_id = request.data.get('contract_id')
                contract = Contract.objects.get(pk=contract_id)
                if ContractDocument.objects.filter(contract=contract).exists():
                    contract_document = ContractDocument.objects.get(contract=contract)
                    contract_document.url = file_path
                    contract_document.name = request.data.get('name')
                    contract_document.updated_by = request.data.get('updated_by', user_id)
                    contract_document.updated_at = request.data.get('updated_at')
                    contract_document.save()
                else:
                    contract_document = ContractDocument.objects.create(
                        contract=contract,
                        url=file_path,
                        name=request.data.get('name'),
                        status=request.data.get('status'),
                        created_by=request.data.get('created_by', user_id),
                        updated_by=request.data.get('updated_by', user_id),
                        created_at=request.data.get('created_at'),
                        updated_at=request.data.get('updated_at'),
                    )
                    contract_document.save()
                result_obj = {'contract_document': model_to_dict(contract_document)}

            if result_obj is not None:
                data = {
                    **result_obj,
                    'file_location': file_path,
                    'file_type': file_extension
                }
            else:
                data = {
                    'file_location': file_path,
                    'file_type': file_extension
                }

            return Response({
                'status': 'OK',
                'data': data
            }, status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
