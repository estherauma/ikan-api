from rest_framework import serializers
from .models import AggregatedContent, MessagingContent, PushNotificationsContent


class AggregatedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedContent
        fields = '__all__'


class MessageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessagingContent
        fields = '__all__'


class PushNotificationsContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationsContent
        fields = '__all__'
