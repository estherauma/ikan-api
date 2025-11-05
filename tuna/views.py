import os
from django.http import HttpResponse
from decouple import config
from rest_framework.response import Response
from rest_framework.decorators import api_view
import django
from django.db.utils import OperationalError
from tuna.serializers import UploadFileSerializer, UploadTemporaryFileSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from vessels.models import Vessel, VesselImage
from contracts.models import Contract, ContractDocument, ContractClause
from django.forms.models import model_to_dict
from mydocuments.models import Passport, Document
import json
from django.utils.dateparse import parse_datetime
from common.utils import upload_file_to_gcs, bucket

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
        'contract': 'contracts',
        'contract_clause_attachment': 'contract_clause_attachments',
        'passport': 'passports',
        'profile_picture': 'profiles',
        'vessel_image': 'vessel_images',
        'my_document': 'my_documents',
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

            updated_at = request.data.get('updated_at')
            updated_at = parse_datetime(updated_at) if updated_at else None

            # write the file to the right path
            # the _ikan_ prefix is used in the mobile app to get the file name
            file = file_serializer.validated_data['file_content']
            file_path = self.upload_paths[request.data['entity_type']] + '/' + str(user_id) + '_ikan_' +\
                file_serializer.validated_data['file_content'].name
            # get extension from file name
            file_extension = os.path.splitext(file_path)[1]
            # Disable local saving of file
            # with open(file_path, 'wb+') as destination:
            #     for chunk in file_serializer.validated_data['file_content'].chunks():
            #         destination.write(chunk)

            result_obj = None
            if request.data['entity_type'] == 'profile_picture':
                # save to gcs
                user.profile_image.storage.save(file_path, file)
                user.profile_image.name = file_path
                user.save()
            elif request.data['entity_type'] == 'vessel_image':
                vessel_id = request.data.get('vessel_id')
                vessel = Vessel.objects.get(pk=vessel_id)
                if VesselImage.objects.filter(vessel=vessel).exists():
                    vessel_image = VesselImage.objects.get(vessel=vessel)
                    if (
                        vessel_image.updated_at is None
                        or updated_at is None
                        or updated_at > vessel_image.updated_at
                    ):
                        # save to gcs
                        vessel_image.image_url.storage.save(file_path, file)
                        vessel_image.image_url.name = file_path
                        vessel_image.description = request.data.get('description')
                        vessel_image.updated_by = request.data.get('updated_by', user_id)
                        vessel_image.updated_at = request.data.get('updated_at')
                        vessel_image.save()
                else:
                    vessel_image = VesselImage.objects.create(
                        app_ref=request.data.get('app_ref'),
                        vessel=vessel,
                        description=request.data.get('description'),
                        created_by=request.data.get('created_by', user_id),
                        updated_by=request.data.get('updated_by', user_id),
                        created_at=request.data.get('created_at'),
                        updated_at=request.data.get('updated_at'),
                    )
                    # save to gcs
                    vessel_image.image_url.storage.save(file_path, file)
                    vessel_image.image_url.name = file_path
                    vessel_image.save()
                result_obj = {'vessel_image': model_to_dict(vessel_image)}
            elif request.data['entity_type'] == 'contract':
                contract_id = request.data.get('contract_id')
                contract = Contract.objects.get(pk=contract_id)
                if ContractDocument.objects.filter(contract=contract).exists():
                    contract_document = ContractDocument.objects.get(contract=contract)
                    if (
                        contract_document.updated_at is None
                        or updated_at is None
                        or updated_at > contract_document.updated_at
                    ):
                        # save to gcs
                        contract_document.url.storage.save(file_path, file)
                        contract_document.url.name = file_path
                        contract_document.name = request.data.get('name')
                        contract_document.updated_by = request.data.get('updated_by', user_id)
                        contract_document.updated_at = request.data.get('updated_at')
                        contract_document.save()
                else:
                    contract_document = ContractDocument.objects.create(
                        contract=contract,
                        name=request.data.get('name'),
                        status=request.data.get('status'),
                        created_by=request.data.get('created_by', user_id),
                        updated_by=request.data.get('updated_by', user_id),
                        created_at=request.data.get('created_at'),
                        updated_at=request.data.get('updated_at'),
                    )
                    # save to gcs
                    contract_document.url.storage.save(file_path, file)
                    contract_document.url.name = file_path
                    contract_document.save()
                result_obj = {'contract_document': model_to_dict(contract_document)}
            elif request.data['entity_type'] == 'passport':
                passport_id = request.data.get('passport_id')
                passport = Passport.objects.get(pk=passport_id)
                # save to gcs
                passport.image_url.storage.save(file_path, file)
                passport.image_url.name = file_path
                passport.save()
            elif request.data['entity_type'] == 'contract_clause_attachment':
                clause_app_ref = request.data.get('clause_app_ref')
                content_field = request.data.get('content_field')

                saved_clause = ContractClause.objects.get(app_ref=clause_app_ref)
                saved_content = json.loads(saved_clause.content)
                # save to gcs
                upload_file_to_gcs(file, file_path)
                saved_content[content_field] = file_path
                saved_clause.content = json.dumps(saved_content)
                saved_clause.save()
            elif request.data['entity_type'] == 'my_document':
                doc_id = request.data.get('doc_id')
                doc = Document.objects.get(pk=doc_id)
                if Document.objects.filter(pk=doc_id).exists():
                    if (
                        doc.updated_at is None
                        or updated_at is None
                        or updated_at > doc.updated_at
                    ):
                        # save to gcs
                        doc.file_url.storage.save(file_path, file)
                        doc.file_url.name = file_path
                        doc.file_name = request.data.get('file_name')
                        doc.file_size = request.data.get('file_size')
                        doc.doc_type = request.data.get('doc_type')
                        doc.updated_by = request.data.get('updated_by', user_id)
                        doc.updated_at = request.data.get('updated_at')
                        doc.save()
                else:
                    doc = Document.objects.create(
                        app_ref=request.data.get('app_ref'),
                        user=user,
                        file_name=request.data.get('file_name'),
                        file_size=request.data.get('file_size'),
                        doc_type=request.data.get('doc_type'),
                        created_by=request.data.get('created_by', user_id),
                        updated_by=request.data.get('updated_by', user_id),
                        created_at=request.data.get('created_at'),
                        updated_at=request.data.get('updated_at'),
                    )
                    # save to gcs
                    doc.file_url.storage.save(file_path, file)
                    doc.file_url.name = file_path
                    doc.save()
                result_obj = {'document': model_to_dict(doc)}

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


class DownloadFileView(APIView):
    permission_classes = ([IsAuthenticated, ])

    def get(self, request):
        url = request.GET.get('url')
        if not url:
            return HttpResponse('Missing URL', status=400)

        blob = bucket.blob(url)
        if not blob.exists():
            return HttpResponse('File not found', status=404)

        content_type = blob.content_type or 'application/octet-stream'
        filename = url.split('/')[-1]
        content = blob.download_as_bytes()
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class UploadTempFileView(APIView):
    permission_classes = ([IsAuthenticated, ])

    def post(self, request):
        file_serializer = UploadTemporaryFileSerializer(data=request.data)
        if file_serializer.is_valid():
            temp_path = 'uploads/temp_files'
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            user_id = request.user.id
            file = file_serializer.validated_data['file_content']
            file_name = file.name
            file_path = os.path.join(temp_path, f"{user_id}_ikan_{file_name}")
            file_path = os.path.normpath(file_path)

            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            return Response({
                'status': 'OK',
                'file_location': file_path,
            }, status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
