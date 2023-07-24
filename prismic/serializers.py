from rest_framework import serializers
from .models import AggregatedContent, MessagingContent


class AggregatedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedContent
        fields = '__all__'


class MessageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessagingContent
        fields = '__all__'
