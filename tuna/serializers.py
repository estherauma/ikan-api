from rest_framework import serializers


class UploadFileSerializer(serializers.Serializer):
    file_content = serializers.FileField(required=True)
    entity_type = serializers.CharField(max_length=255, required=True)
