from rest_framework import serializers
from accounts.models import User, UserBank, UserBeneficiaries
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from common.twilio import OTPVerification


class LoginSerializer(serializers.Serializer):
    '''Login user serializer '''
    email = serializers.CharField(required=False, write_only=True)
    phone_number = serializers.CharField(required=False, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)


class RegisterSerializer(serializers.Serializer):
    '''Register user serializer '''
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    profile_image = serializers.URLField(required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')

        try:
            validate_email(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'profile_image')


class PasswordResetCheckTokenSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    reset_password_token = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        reset_password_token = data.get('reset_password_token')
        try:
            user = User.objects.get(email=email)
            if user.reset_password_token != reset_password_token:
                raise serializers.ValidationError("Invalid reset password token.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    reset_password_token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        reset_password_token = data.get('reset_password_token')
        try:
            user = User.objects.get(email=email)
            if user.reset_password_token != reset_password_token:
                raise serializers.ValidationError("Invalid reset password token.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
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
    user_id = serializers.CharField(max_length=36)

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must start with a '+' sign and include the country code.")
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits after the country code."
            )
        return value

    def start_otp_process(self):
        try:
            phone_number = self.validated_data['phone_number']
            otp_service = OTPVerification()
            response = otp_service.send_otp(phone_number)
            return response
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=15, required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    user_id = serializers.CharField(max_length=36)
    type = serializers.CharField(max_length=20)
    # change to choice field; mobile and telephone
    # type = serializers.ChoiceField(choices=['mobile', 'telephone'])

    def validate_phone_number(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must start with a '+'"
                "sign and include the country code."
            )
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only "
                "digits after the country code."
            )
        return value

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                'OTP must be a number'
            )

        if len(value) < 4:
            raise serializers.ValidationError(
                'OTP must be 4 characters long'
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
