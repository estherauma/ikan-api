import json
import secrets
import string
from accounts.models import User
from common.email import TunaEmailHelper, EmailTemplate
from rest_framework.response import Response
from rest_framework import status
import uuid
from datetime import datetime, date
import os
from google.cloud import storage
from datetime import timedelta


storage_client = storage.Client()
bucket_name = os.environ.get("GS_BUCKET_NAME")
if bucket_name is None:
    raise ValueError("GS_BUCKET_NAME environment variable is not set.")
bucket = storage_client.bucket(bucket_name)


def write_json_to_file(file_name, data, mode='w'):
    # This is purely for debugging
    # We can use it if we ever need to write to a file
    with open(file_name, mode) as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def get_access_code(length=10):
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    access_code = ''.join(secrets.choice(characters) for _ in range(length))
    return access_code.upper()


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def send_email_invite(user, auth_common_text=None):
    email_helper = TunaEmailHelper()
    send_success = email_helper.tuna_send_email(
        to_emails=[user.email],
        subject='IKAN: Invitation to join IKAN',
        body={
            'email': user.email,
            'access_token': user.access_code,
        },
        template=EmailTemplate.ACCESS_TOKEN.value,
        auth_common_text=auth_common_text,
    )
    if send_success:
        return Response(
            {
                'status': 'OK',
                'message': 'User invited successfully.'
            },
            status.HTTP_200_OK
        )
    else:
        return Response(
            {
                'status': 'FAIL',
                'message': 'Failed to send invitation email.'
            },
            status.HTTP_400_BAD_REQUEST
        )


def get_user_from_post_request(request):
    try:
        if request.data['user_id'] is not None:
            try:
                user = User.objects.get(pk=request.data['user_id'])
                return user.id
            except User.DoesNotExist:
                return None
    except KeyError:
        return None


def get_user_from_get_request(request):
    if request.GET.get('user_id') is not None:
        try:
            user = User.objects.get(pk=request.GET.get('user_id'))
            return user
        except User.DoesNotExist:
            return None
    else:
        return request.user.id


def generate_uuid():
    random_uuid = str(uuid.uuid4())
    return random_uuid


def format_local_date(value, current_language='en-us'):
    if not value:
        return value

    format_str = '%d %b %Y'

    if current_language == 'qm-zh':
        format_str = '%Y年%m月%d日'

    if isinstance(value, (datetime, date)):
        dt = value
    elif isinstance(value, str):
        value = value.strip()
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    else:
        return value

    return dt.strftime(format_str)


def upload_file_to_gcs(file, file_path):
    """Uploads a file to the given GCS path."""

    # Create a new blob and upload the file's content.
    blob = bucket.blob(file_path)
    blob.upload_from_file(file)
    return blob.public_url


def get_gcs_signed_url(file_path, hours=1):
    """Generates a signed URL for a file in GCS."""
    if not file_path:
        return None

    blob = bucket.blob(file_path)

    url = blob.generate_signed_url(
        expiration=timedelta(hours=hours),
    )
    return url


def split_string_by_comma(string):
    # split string by comma and remove any leading or trailing spaces
    if string is None:
        return []
    return [item.strip() for item in string.split(',')] if string else []
