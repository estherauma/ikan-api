from rest_framework import serializers

# model imports
from contracts.models import Contract, ContractClause, ContractDocument


class ContractSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    app_ref = serializers.CharField(required=True)
    internal_ref = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    description = serializers.CharField(required=False)
    taiwanese_company = serializers.CharField(required=False)
    indonesian_company = serializers.CharField(required=False)
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


class contractClauseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    order = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)

    class Meta:
        model = ContractClause
        fields = '__all__'

    def create(self, validated_data):
        contract_instance = validated_data['contract']
        if isinstance(contract_instance, Contract):
            return ContractClause.objects.create(**validated_data)

        try:
            contract_instance = Contract.objects.get(id=contract_instance)
        except Contract.DoesNotExist:
            raise serializers.ValidationError("Contract with the specified ID does not exist")

        validated_data['contract'] = contract_instance
        return ContractClause.objects.create(**validated_data)

    def validate_contract(self, contract):
        if not isinstance(contract, Contract):
            raise serializers.ValidationError("Invalid contract data")
        return contract
