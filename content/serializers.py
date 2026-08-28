from rest_framework import serializers

from content.models import AggregatedContent


class AggregatedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedContent
        fields = "__all__"
