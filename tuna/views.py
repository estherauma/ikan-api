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
from django.db.models import Q
from mydocuments.models import Passport, Document
import json
from django.utils.dateparse import parse_datetime
from common.utils import upload_file_to_gcs, bucket, get_gcs_signed_url

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
            updated_by_instance = User.objects.get(pk=request.data.get('updated_by')) \
                if request.data.get('updated_by') else None
            created_by_instance = User.objects.get(pk=request.data.get('created_by')) \
                if request.data.get('created_by') else None

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
                if vessel_id is None and request.data.get('vessel_app_ref') is not None:
                    vessel_app_ref = request.data.get('vessel_app_ref')
                    vessel = Vessel.objects.get(app_ref=vessel_app_ref)
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
                        created_by=created_by_instance if created_by_instance else user,
                        updated_by=updated_by_instance if updated_by_instance else user,
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
                if contract_id is None and request.data.get('contract_app_ref') is not None:
                    contract_app_ref = request.data.get('contract_app_ref')
                    contract = Contract.objects.get(app_ref=contract_app_ref)
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
                        contract_document.updated_by = updated_by_instance if updated_by_instance else user
                        contract_document.updated_at = request.data.get('updated_at')
                        contract_document.save()
                else:
                    contract_document = ContractDocument.objects.create(
                        contract=contract,
                        name=request.data.get('name'),
                        status=request.data.get('status'),
                        created_by=created_by_instance if created_by_instance else user,
                        updated_by=updated_by_instance if updated_by_instance else user,
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
                        doc.updated_by = updated_by_instance if updated_by_instance else user
                        doc.updated_at = request.data.get('updated_at')
                        doc.save()
                else:
                    doc = Document.objects.create(
                        app_ref=request.data.get('app_ref'),
                        user=user,
                        file_name=request.data.get('file_name'),
                        file_size=request.data.get('file_size'),
                        doc_type=request.data.get('doc_type'),
                        created_by=created_by_instance if created_by_instance else user,
                        updated_by=updated_by_instance if updated_by_instance else user,
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
    """
    DEPRECATED / WARNING:
    This view reads and buffers the entire file into server memory (RAM) before returning it.
    Downloading large files or handling concurrent requests here can trigger high memory usage
    and cause Out-Of-Memory (OOM) server crashes.

    Use the signed-url endpoint (DownloadFileSignedUrlView) which offloads
    file transfer directly to Google Cloud Storage.
    """
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


def _clause_content_matches_path(content, file_path):
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (TypeError, ValueError):
            return file_path in content
    if isinstance(content, dict):
        return file_path in content.values()
    if isinstance(content, list):
        return file_path in content
    return False


def _worker_vessel_app_refs(user):
    # Vessels a worker is assigned to via the fisher-requirement clause of a contract they can access
    clauses = ContractClause.objects.filter(
        contract__contract_user_access__user=user,
        contract__contract_user_access__is_active=True,
        kind='contract-clauses-parties-requirement-fishers',
    ).values_list('content', flat=True)
    refs = []
    for content in clauses:
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except (TypeError, ValueError):
                continue
        if isinstance(content, dict) and content.get('vessel'):
            refs.append(content['vessel'])
    return refs


def user_can_access_file(user, file_path):
    """Verify file_path belongs to a record the user owns or otherwise has access to."""
    if user.is_superuser:
        return True

    if user.profile_image and user.profile_image.name == file_path:
        return True

    if Document.objects.filter(user=user, file_url=file_path).exists():
        return True

    if Passport.objects.filter(user=user, image_url=file_path).exists():
        return True

    accessible_contracts = Contract.objects.filter(
        Q(created_by=user) | Q(contract_user_access__user=user, contract_user_access__is_active=True)
    )
    if ContractDocument.objects.filter(url=file_path, contract__in=accessible_contracts).exists():
        return True

    clause_contents = ContractClause.objects.filter(contract__in=accessible_contracts).values_list('content', flat=True)
    if any(_clause_content_matches_path(content, file_path) for content in clause_contents):
        return True

    vessel_app_refs = _worker_vessel_app_refs(user)
    if VesselImage.objects.filter(image_url=file_path).filter(
        Q(vessel__created_by=user) | Q(vessel__app_ref__in=vessel_app_refs)
    ).exists():
        return True

    return False


class DownloadFileSignedUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        file_path = request.GET.get('url')
        if not file_path:
            return Response({'error': 'Missing URL parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Verify file access permissions
        # if not user_can_access_file(request.user, file_path):
        #     return Response({'error': 'File not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

        blob = bucket.blob(file_path)
        if not blob.exists():
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        signed_url = get_gcs_signed_url(file_path, hours=0.25)
        if not signed_url:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'gcs_signed_url': signed_url}, status=status.HTTP_200_OK)


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
