from accounts.models import LoginEvent, User, UserBank, UserBeneficiaries
from accounts.serializers import (
    LoginSerializer, RegisterSerializer,
    PasswordResetCheckTokenSerializer,
    PasswordResetSerializer, UserBeneficiarySerializer, UserProfileSerializer,
    UserSerializer, UserBankDetailsSerializer
)

from common.email import TunaEmailHelper, EmailTemplate
from common.jwt_manager import JwtManager
from common.utils import get_access_code, get_user_from_get_request, get_user_from_post_request, send_email_invite

from decouple import config

from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView


import random

from companies.models import Company, UserCompany
from companies.serializers import UserCompanySerializer


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """
            Log in a user using their email and password.

            :param request: The HTTP request object.
            :type request: HttpRequest

            :param email: The email address of the user.
            :type email: str

            :param password: The user's password.
            :type password: str

            :return: The HTTP response.
            :rtype: HttpResponse

            **Sample Request**:

                POST /login/ HTTP/1.1
                Host: example.com
                Content-Type: application/json

                {
                    "email": "user@example.com",
                    "password": "securepassword"
                }
        """
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        is_first_login = False

        email = data.get('email')
        password = data.get('password')
        user = User.objects.filter(email=email).first()
        if user:
            if user.is_active:
                if user.check_password(password):
                    identity_manager = JwtManager()
                    if user.groups.exists():
                        payload = {
                            'email': user.email,
                            'id': user.pk,
                            'firstName': user.first_name,
                            'lastName': user.last_name,
                            'isAdmin': user.is_admin,
                            'role': list(user.groups.values_list('name', flat=True))[0],
                            'roles': list(user.groups.values_list('name', flat=True)) if user.groups.exists() else [],
                        }
                        token = identity_manager.encode(payload)
                        is_first_login = user.last_login is None
                        user.last_login = timezone.now()
                        user.save()
                        LoginEvent.objects.create(
                            user=user, ip_address=request.META['REMOTE_ADDR'])
                    else:
                        raise AuthenticationFailed('Authentication failed, contact admin', 401)
                else:
                    raise AuthenticationFailed('Invalid password, please try again', 401)
            else:
                raise AuthenticationFailed('User account is not activated, contact admin', 401)
        else:
            raise AuthenticationFailed('User does not exist', 401)
        return Response({
            'status': 'OK',
            'data': {
                'token': token,
                'is_first_login': is_first_login,
                'user_data': payload,
            }
        },
            status.HTTP_200_OK
        )


class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request):
        '''Register a user
        Args:
            request(Request): HTTP request
        '''
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False)

        # Send verification email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_link = f'{config("BASE_URL")}/api/v1/accounts/verify-email/{uid}/{token}'
        email_helper = TunaEmailHelper()
        email_helper.tuna_send_email(
            to_emails=[user.email],
            subject='Verify your email to start using IKAN',
            body={
                'first_name': user.first_name,
                'verification_link': verification_link,
            },
            template=EmailTemplate.VERIFY_EMAIL.value,
        )

        return Response(
            {
                'status': 'OK',
                'message': 'Account created successfully. Please check your email to verify your account.'
            },
            status.HTTP_201_CREATED
        )


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            notify_admin(user)
            return redirect('verify-email-success')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass
    return redirect('verify-email-failure')


def notify_admin(user):
    message = f"A new user {user.email} has registered and needs activation."
    admin_email = config('ADMIN_EMAIL')
    email_helper = TunaEmailHelper()
    email_helper.tuna_send_email(
        to_emails=[config('ADMIN_EMAIL')],
        subject='IKAN: New user registration',
        body=message,
    )


def verify_email_success(request):
    return render(request, template_name='verify-email/success.html')


def verify_email_failure(request):
    return render(request, template_name='verify-email/failure.html')


class RequestPasswordReset(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'status': 'FAIL',
                'message': 'Email is required',
            }, status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if user:
            password_rest_token = random.randrange(11111, 99999,)
            user.reset_password_token = password_rest_token
            user.save()

            email_helper = TunaEmailHelper()
            email_helper.tuna_send_email(
                to_emails=[user.email],
                subject='Reset your IKAN password',
                body={
                    'first_name': user.first_name,
                    'password_rest_token': password_rest_token,
                },
                template=EmailTemplate.PASSWORD_RESET_REQUEST.value,
            )

        return Response(
            {
                'status': 'OK',
                'message': 'Password reset request was successful. Please check your email for the password reset code.'
            },
            status.HTTP_200_OK
        )


class PasswordResetCheckToken(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            data = request.data
            serializer = PasswordResetCheckTokenSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            return Response(
                {
                    'status': 'OK',
                    'message': 'Password reset token confirmed'
                },
                status.HTTP_200_OK
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return Response(
            {
                'status': 'ERROR',
                'message': 'Password reset failed.'
            },
            status.HTTP_400_BAD_REQUEST
        )


class ResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            data = request.data
            serializer = PasswordResetSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            email = request.data.get('email')
            password = request.data.get('password')
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(password)
                user.reset_password_token = None
                user.save()
                return Response(
                    {
                        'status': 'OK',
                        'message': 'Password reset successful.'
                    },
                    status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'ERROR',
                        'error': 'User does not exist'
                    },
                    status.HTTP_400_BAD_REQUEST
                )

        except (TypeError, ValueError, OverflowError):
            pass
        return Response(
            {
                'status': 'ERROR',
                'message': 'Password reset failed.',
            },
            status.HTTP_400_BAD_REQUEST
        )


class VerifyAndSetPassword(APIView):
    def post(self, request):
        '''Verify a user and set password
        Args:
            request(Request): HTTP request
        '''
        data = request.data
        access_code = data.get('access_code')
        '''
            access code field on the db can be blank or null.
            So we need to check for None so we don't get back all records for users
            who have already verified and set their passwords
        '''
        if access_code is None:
            return Response(
                {
                    'status': 'Failed',
                    'message': 'Access code is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(access_code=access_code)
            user.is_verified = True
            user.is_active = True
            if data.get('password') == data.get('password_confirm'):
                user.set_password(data.get('password'))
                user.access_code = None
                user.save()
                notify_admin(user)
                return Response(
                    {
                        'status': 'OK',
                        'message': 'Account verified and password set successfully.'
                    },
                    status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'ERROR',
                        'message': 'Passwords do not match.'
                    },
                    status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Invalid access code.'
                },
                status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(APIView):
    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        user = self.get_user(pk)
        serializer = UserSerializer(user)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        })


class InviteUser(APIView):
    def post(self, request):
        '''Invite a user
        Args:
            request(Request): HTTP request
        '''
        data = request.data
        email = data.get('email')
        role = data.get('role')
        if email is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Email is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        if role is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Role is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        user_exists = User.objects.filter(email=email).exists()
        if not user_exists:
            serializer = RegisterSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.create_user(
                email=email,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                access_code=get_access_code(),
                is_verified=False,
                is_active=False,
            )

            group = Group.objects.get(name=data.get('role'))
            user.groups.add(group)

            return send_email_invite(user)
        else:
            user = User.objects.get(email=email)

            if not user.is_verified and not user.is_active:
                return send_email_invite(user)
            else:
                return Response(
                    {
                        'status': 'OK',
                        'message': 'User already invited.'
                    },
                    status.HTTP_200_OK
                )


class UserListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        role = request.GET.get('role')
        if role is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Role is required.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        try:
            Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Invalid role.'
                },
                status.HTTP_400_BAD_REQUEST
            )
        users = User.objects.filter(groups__name=role, created_by=request.user.id)
        serializer = UserProfileSerializer(users, many=True)

        # get all roles for each user and add to response data
        for user_data in serializer.data:
            user = User.objects.get(id=user_data['id'])
            user_data['roles'] = list(user.groups.values_list('name', flat=True)) if user.groups.exists() else []

        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        })


class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        # if request has a query param of user id, then get that user instead
        user_id = request.GET.get('user_id')
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
        serializer = UserProfileSerializer(user)

        # Add role to response data
        roles = list(user.groups.values_list('name', flat=True)) if user.groups.exists() else []
        resp_data = {**serializer.data, 'roles': roles}

        return Response({
            'status': 'OK',
            'data': resp_data,
            'errors': []
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        try:
            # register new user profile
            if request.query_params.get('register') == 'register':
                user_exists = User.objects.filter(email=request.data['email']).exists()
                if user_exists:
                    user = User.objects.get(email=request.data['email'])
                    user_id = user.id
                else:
                    if request.data['user_role'] is None:
                        return Response(
                            {
                                'status': 'FAIL',
                                'message': 'Role is required.'
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        new_user = User.objects.create_user(
                            email=request.data['email'],
                            first_name=request.data['first_name'],
                            last_name=request.data['last_name'],
                            access_code=get_access_code(),
                            is_verified=False,
                            is_active=False,
                        )
                        role = request.data['user_role']
                        group = Group.objects.get(name=role)
                        new_user.groups.add(group)

                        user_id = new_user.id
            elif request.data['user_id'] is not None:
                try:
                    user = User.objects.get(pk=request.data['user_id'], email=request.data['email'])
                    user_id = user.id
                except User.DoesNotExist:
                    return Response(
                        {
                            'status': 'FAIL',
                            'message': 'User not found.'
                        },
                        status.HTTP_404_NOT_FOUND
                    )
        except KeyError:
            user_id = request.user.id

        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
        data = request.data
        serializer = UserProfileSerializer(user, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Add role to response data
        roles = list(user.groups.values_list('name', flat=True)) if user.groups.exists() else None
        resp_data = {**serializer.data, 'roles': roles}
        return Response({
            'status': 'OK',
            'data': resp_data,
            'errors': []
        }, status=status.HTTP_200_OK)


class UpdateUserCompany(APIView):
    """
    API endpoint for updating user-company relationships.

    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get user companies.

        If a 'user_id' query parameter is provided, retrieve companies for that user.
        If the user is not found, return a 404 response.

        Returns a list of user companies along with their details.
        """
        user = request.user.id
        # if request has a query param of user id, then get that user instead
        user_id = request.GET.get('user_id')
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        'status': 'FAIL',
                        'message': 'User not found.'
                    },
                    status.HTTP_404_NOT_FOUND
                )
       # get user companies
        user_companies = UserCompany.objects.filter(user=user)
        serializer = UserCompanySerializer(user_companies, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create or update a user-company relationship.

        Requires 'user_id', 'company_id', 'role', 'start_date', and 'end_date' in the request data.
        Check if the user and company exist, return a 404 response if not.
        Check if the user is already linked to the company, return a 400 response if true.
        If the user is linked to other companies, mark them as inactive.

        Returns the details of the created or updated user-company relationship.
        """
        user_id = request.data['user_id']
        company_id = request.data['company_id']

        # check if user exists and return if not
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        # check if company exists and return if not
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Company not found.'
                },
                status.HTTP_404_NOT_FOUND
            )

        # check if user is already linked to company and if they are return
        user_company_exists = UserCompany.objects.filter(user=user, company=company).exists()
        if user_company_exists:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User already linked to company.'
                },
                status.HTTP_400_BAD_REQUEST
            )

        # if not linked, check other company linkages and mark them as inactive
        user_company_exists = UserCompany.objects.filter(user=user, is_active=True).exists()
        if user_company_exists:
            user_company = UserCompany.objects.get(user=user, is_active=True)
            user_company.is_active = False
            user_company.save()

        # add entry to Usercompany
        user_company = UserCompany.objects.create(
            user=user,
            company=company,
            role=request.data['role'],
            start_date=request.data['start_date'],
            end_date=request.data['end_date'],
        )
        user_company.save()
        serializer = UserCompanySerializer(user_company)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'errors': []
        }, status=status.HTTP_200_OK)


class UserBankDetailsApiView(APIView):
    """
    Manage user bank account details
    Requires authentication
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get user banks.
        If a `user_id` param is passed, retrive the companies for that user.
        If not, it'll return companies of that user
        """
        user = get_user_from_get_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            user_banks = UserBank.objects.filter(user=user)
            serializer = UserBankDetailsSerializer(user_banks, many=True)
            return Response({
                'status': 'OK',
                'data': serializer.data,
                'errors': []
            }, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_post_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            serializer_data = {**request.data, 'user': user}
            serializer = UserBankDetailsSerializer(data=serializer_data)

            if serializer.is_valid():
                # check if user already has account details and mark them as inactive
                user_bank_exists = UserBank.objects.filter(user=user, is_active=True).exists()
                if user_bank_exists:
                    user_bank = UserBank.objects.get(user=user, is_active=True)
                    user_bank.is_active = False
                    user_bank.save()
                # check if user has account with the same account name and number
                similar_bank_exists = UserBank.objects.filter(
                    user=user, account_name=request.data['account_name'],
                    account_number=request.data['account_number']).exists()

                if similar_bank_exists:
                    return Response({
                        'status': 'FAIL',
                        'message': 'User bank account exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
                return Response({
                    'status': 'OK',
                    'data': serializer.data,
                    'errors': []
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'FAIL',
                    'data': [],
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)


class UserBeneficiariesApiView(APIView):
    """
    Manage user beneficiaries
    Requires authentication
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = get_user_from_get_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            user_beneficiaries = UserBeneficiaries.objects.filter(user=user)
            serializer = UserBeneficiarySerializer(user_beneficiaries, many=True)
            return Response({
                'status': 'OK',
                'data': serializer.data,
                'errors': []
            }, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_post_request(request)
        if user is None:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'User not found.'
                },
                status.HTTP_404_NOT_FOUND
            )
        else:
            serializer_data = {**request.data, 'user': user}
            serializer = UserBeneficiarySerializer(data=serializer_data)
            if serializer.is_valid():
                # check if user has beneficiary with the same account number
                beneficiary_exists = UserBeneficiaries.objects.filter(
                    user=user, account_number=request.data['account_number']).exists()
                if beneficiary_exists:
                    return Response(
                        {
                            'status': 'FAIL',
                            'message': 'Beneficiary with the same account number already exists.'
                        },
                        status.HTTP_400_BAD_REQUEST
                    )
                else:
                    serializer.save()
                    return Response({
                        'status': 'OK',
                        'data': serializer.data,
                        'errors': []
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'FAIL',
                    'data': [],
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
