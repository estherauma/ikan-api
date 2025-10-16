from rest_framework import serializers
from wages.models import Wage


class WageSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()

    class Meta:
        model = Wage
        fields = '__all__'
