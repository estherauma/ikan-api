from rest_framework import serializers
from companies.models import Company, UserCompany


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        exclude = ['logo_url']


class UserCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCompany
        fields = '__all__'
