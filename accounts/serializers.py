from rest_framework import serializers
from accounts.models import User, UserBank, UserBeneficiaries
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from common.twilio import OTPVerification, check_verification_code
from django.db.models import Q


class LoginSerializer(serializers.Serializer):
    '''Login user serializer '''
    email = serializers.CharField(required=False, write_only=True)
    phone_number = serializers.CharField(required=False, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)


class RegisterSerializer(serializers.Serializer):
    '''Register user serializer '''
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    profile_image = serializers.URLField(required=False)

    def __init__(self, *args, **kwargs):
        self.auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(self.auth_common_text.get('emailAlreadyExists', 'Email already exists.'))

        if value:
            try:
                validate_email(value)
            except serializers.ValidationError:
                raise serializers.ValidationError(self.auth_common_text.get('invalidEmailAddress',
                                                                            'Invalid email address.'))

        return value

    def validate_phone_number(self, value):
        if value and User.objects.filter(Q(telephone=value) | Q(mobile=value)).exists():
            raise serializers.ValidationError(self.auth_common_text.get('phoneNumberAlreadyExists',
                                                                        'Phone number already exists.'))

        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustStartWithCode',
                                          'Phone number must start with a \'+\' sign and include the country code.'))
        if value and not value[1:].isdigit():
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustContainOnlyDigits',
                                          'Phone number must contain only digits after the country code.'))
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')

        if not email and not phone_number:
            raise serializers.ValidationError(self.auth_common_text.get('emailOrPhoneNumberRequired',
                                                                        'Either email or phone number is required.'))

        return data

    def create(self, validated_data):
        if not validated_data.get('mobile') and validated_data.get('phone_number'):
            validated_data['mobile'] = validated_data['phone_number']
        if validated_data.get('phone_number'):
            del validated_data['phone_number']
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'profile_image')


class PasswordResetCheckTokenSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    reset_password_token = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        self.auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)

    def validate_email(self, value):
        if value:
            try:
                validate_email(value)
            except serializers.ValidationError:
                raise serializers.ValidationError(self.auth_common_text.get('invalidEmailAddress',
                                                                            'Invalid email address.'))

        return value

    def validate_phone_number(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustStartWithCode',
                                          "Phone number must start with a '+' sign and include the country code.")
            )
        if value and not value[1:].isdigit():
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustContainOnlyDigits',
                                          "Phone number must contain only digits after the country code.")
            )
        return value

    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        reset_password_token = data.get('reset_password_token')

        if not email and not phone_number:
            raise serializers.ValidationError(self.auth_common_text.get('emailOrPhoneNumberRequired',
                                                                        'Either email or phone number is required.'))

        if email:
            user = User.objects.get(email=email)
            if user.reset_password_token != reset_password_token:
                raise serializers.ValidationError(self.auth_common_text.get('invalidResetPasswordToken',
                                                                            'Invalid reset password token.'))
        elif phone_number:
            # user = User.objects.get(Q(mobile=phone_number) | Q(telephone=phone_number))
            res = check_verification_code(self.context.get('request'), phone_number, reset_password_token)
            if not res:
                raise serializers.ValidationError(self.auth_common_text.get('invalidResetPasswordCode',
                                                                            'Invalid reset password code.'))
        else:
            raise serializers.ValidationError(self.auth_common_text.get('userDoesNotExist',
                                                                        'User does not exist.'))
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    reset_password_token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        self.auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)

    def validate_email(self, value):
        if value:
            try:
                validate_email(value)
            except serializers.ValidationError:
                raise serializers.ValidationError(self.auth_common_text.get('invalidEmailAddress',
                                                                            'Invalid email address.'))

        return value

    def validate_phone_number(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustStartWithCode',
                                          "Phone number must start with a '+' sign and include the country code."))
        if value and not value[1:].isdigit():
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustContainOnlyDigits',
                                          "Phone number must contain only digits after the country code."))
        return value

    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        reset_password_token = data.get('reset_password_token')

        if not email and not phone_number:
            raise serializers.ValidationError(self.auth_common_text.get('emailOrPhoneNumberRequired',
                                                                        'Either email or phone number is required.'))

        if email:
            user = User.objects.get(email=email)
            if user.reset_password_token != reset_password_token:
                raise serializers.ValidationError(self.auth_common_text.get('invalidResetPasswordToken',
                                                                            'Invalid reset password token.'))
        elif phone_number:
            # user = User.objects.get(Q(mobile=phone_number) | Q(telephone=phone_number))
            res = check_verification_code(self.context.get('request'), phone_number, reset_password_token)
            if not res:
                raise serializers.ValidationError(self.auth_common_text.get('invalidResetPasswordCode',
                                                                            'Invalid reset password code.'))
        else:
            raise serializers.ValidationError(self.auth_common_text.get('userDoesNotExist',
                                                                        'User does not exist.'))
        return data

    def validate_password(self, value):
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'reset_password_token', 'is_superuser',
                   'is_staff', 'groups', 'access_code', 'user_permissions']
        read_only_fields = ['is_active', 'is_verified', 'is_staff', 'is_superuser',
                            'groups', 'user_permissions', 'access_code', 'reset_password_token', 'email']


class UserBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBank
        fields = '__all__'


class UserBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBeneficiaries
        fields = '__all__'


class OTPGenerateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, required=True)
    user_id = serializers.CharField(max_length=36, required=False)
    locale = serializers.CharField(max_length=5, default='en')

    def __init__(self, *args, **kwargs):
        self.auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustStartWithCode',
                                          "Phone number must start with a '+' sign and include the country code."))
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustContainOnlyDigits',
                                          "Phone number must contain only digits after the country code.")
            )
        return value

    def start_otp_process(self):
        try:
            phone_number = self.validated_data['phone_number']
            locale = self.validated_data.get('locale', 'en')
            otp_service = OTPVerification()
            response = otp_service.send_otp(phone_number, locale)
            return response
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=15, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    user_id = serializers.CharField(max_length=36, required=False)
    type = serializers.CharField(max_length=20, default='mobile')
    # change to choice field; mobile and telephone
    # type = serializers.ChoiceField(choices=['mobile', 'telephone'])

    def __init__(self, *args, **kwargs):
        self.auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustStartWithCode',
                                          "Phone number must start with a '+' sign and include the country code.")
            )
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                self.auth_common_text.get('phoneNumberMustContainOnlyDigits',
                                          "Phone number must contain only digits after the country code.")
            )
        return value

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(self.auth_common_text.get('otpMustBeNumber', 'OTP must be a number'))

        if len(value) < 4:
            raise serializers.ValidationError(
                self.auth_common_text.get('otpMustBeLongEnough', 'OTP must be 4 characters or more long')
            )
        return value

    def verify_otp(self):
        try:
            phone_number = self.validated_data['phone_number']
            otp_code = self.validated_data['otp_code']
            otp_service = OTPVerification()
            response = otp_service.check_otp(otp_code, phone_number)
            return response
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
