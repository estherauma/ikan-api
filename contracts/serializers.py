from rest_framework import serializers

# model imports
from contracts.models import Contract, ContractDocument

class ContractSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    app_ref = serializers.CharField(required=True)
    internal_ref = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    description = serializers.CharField(required=True)
    taiwanese_company = serializers.IntegerField(required=True)
    indonesian_company = serializers.IntegerField(required=True)
    kind = serializers.CharField(required=True)

    class Meta:
        model = Contract
        fields = '__all__'
    
    def create(self, validated_data):
        return Contract.objects.create(**validated_data)
    

class ContractDocumentSerializer(serializers.ModelSerializer):
    contract_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    url = serializers.CharField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = ContractDocument
        fields = '__all__'
    
    def create(self, validated_data):
        return ContractDocument.objects.create(**validated_data)
    
    def validate_contract(self, contract_id):
        if not Contract.objects.filter(id=contract_id).exists():
            raise serializers.ValidationError("Contract does not exist")
        return contract_id