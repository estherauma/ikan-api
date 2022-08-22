from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    '''Login user serializer '''
    email = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)
