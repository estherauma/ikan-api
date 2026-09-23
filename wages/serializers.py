from rest_framework import serializers
from django.utils import timezone
from wages.models import Wage


class WageSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()

    class Meta:
        model = Wage
        fields = '__all__'

    def update(self, instance, validated_data):
        payslip_status_provided = 'payslip_status' in validated_data

        if payslip_status_provided:
            payslip_status = validated_data.get('payslip_status')
            is_signing_payslip = (
                payslip_status == Wage.PAYSLIP_STATUS_SIGNED
                and instance.payslip_status != Wage.PAYSLIP_STATUS_SIGNED
            )
            if is_signing_payslip:
                validated_data['payslip_signed_at'] = timezone.now()
            else:
                validated_data.pop('payslip_signed_at', None)
        else:
            payslip = validated_data.get('payslip', instance.payslip)
            payslip_name = payslip.name if payslip else ''
            if (
                payslip_name
                and '__signed' in payslip_name
                and instance.payslip_status != Wage.PAYSLIP_STATUS_SIGNED
            ):
                validated_data['payslip_status'] = Wage.PAYSLIP_STATUS_SIGNED
                validated_data['payslip_signed_at'] = timezone.now()

        return super().update(instance, validated_data)
