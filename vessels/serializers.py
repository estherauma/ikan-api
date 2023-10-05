from rest_framework import serializers
from vessels.models import Vessel, VesselImage


class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = '__all__'


class VesselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselImage
        fields = '__all__'
