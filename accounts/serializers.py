from rest_framework import serializers
from accounts.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email


class LoginSerializer(serializers.Serializer):
    '''Login user serializer '''
    email = serializers.CharField(required=True, write_only=True)
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
