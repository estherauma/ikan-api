from rest_framework import serializers
from organizations.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ['name', 'description', 'status', 'country', 'city', 'telephone', 'email', 'address_line_1']
        optional_fields = ['logo', 'address_line_2', 'address_line_3']
        