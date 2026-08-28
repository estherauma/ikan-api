from rest_framework import serializers
from vessels.models import Vessel, VesselImage


class VesselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselImage
        fields = '__all__'


class VesselSerializer(serializers.ModelSerializer):
    vessel_image = VesselImageSerializer(read_only=True, source='vessel_image.first')

    class Meta:
        model = Vessel
        fields = '__all__'
