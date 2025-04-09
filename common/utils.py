import json
import secrets
import string
from accounts.models import User
from common.email import TunaEmailHelper, EmailTemplate
from rest_framework.response import Response
from rest_framework import status
import uuid


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


def send_email_invite(user):
    email_helper = TunaEmailHelper()
    send_success = email_helper.tuna_send_email(
        to_emails=[user.email],
        subject='IKAN: Invitation to join IKAN',
        body={
            'email': user.email,
            'access_token': user.access_code,
        },
        template=EmailTemplate.ACCESS_TOKEN.value,
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


def get_clause_order(clause_kind):
    clause_order = {
      'contract-clauses-parties-requirement-vessel': 0,
      'contract-clauses-parties-requirement-fishers': 0.1,
      'contract-clauses-contract-validity': 1,
      'contract-clauses-wage-benefits': 2,
      'contract-clauses-accident-medical-and-life-insurance': 3,
      'contract-clauses-transportation-severance-food-accomodation': 4,
      'contract-clauses-working-hours-rest-and-leave': 5,
      'contract-clauses-labor-protection-and-benefits': 6,
      'contract-clause-requirements-that-party-b-must-comply-with': 7,
      'contract-clauses-means-to-address-breach-of-contract': 8,
      'contract-clauses-dispute-settlement': 9,
      'contract-clauses-miscellaneous': 10,
      'contract-clauses-attachments': 11,
    }
    return clause_order[clause_kind] if clause_kind in clause_order else None


def generate_uuid():
    random_uuid = str(uuid.uuid4())
    return random_uuid
