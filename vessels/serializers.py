from rest_framework import serializers
from vessels.models import Vessel, VesselImage


class VesselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselImage
        fields = '__all__'


class VesselSerializer(serializers.ModelSerializer):
    vessel_image = serializers.SerializerMethodField()

    class Meta:
        model = Vessel
        fields = '__all__'

    def get_vessel_image(self, obj):
        # Uses prefetched list in memory if available, avoids DB query per row
        images = getattr(obj, '_prefetched_objects_cache', {}).get('vessel_image')
        if images is not None:
            image = images[0] if images else None
        else:
            image = obj.vessel_image.first()
        return VesselImageSerializer(image).data if image else None
