from accounts.models import User
from common.models import AuditableModel
from django.db import models
from vessels.models import Vessel


class Payment(AuditableModel):
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE)  # change
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # change to default user
    payment_date = models.DateField()
    payment_category = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=50)
    beneficiary_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField()
    total_usd_amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    cash_usd_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    cash_currency = models.CharField(max_length=255, null=True, blank=True)
    cash_local_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    cash_exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_cash_beneficiary_crew = models.BooleanField(default=False)
    cash_beneficiary_relationship = models.CharField(
        max_length=255, null=True, blank=True
    )
    cash_beneficiary_contact = models.CharField(max_length=255, null=True, blank=True)
    cash_beneficiary_contact_platform = models.CharField(
        max_length=255, null=True, blank=True
    )
    bank_transfer_usd_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bank_transfer_currency = models.CharField(max_length=255, null=True, blank=True)
    bank_transfer_local_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bank_transfer_exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_bank_transfer_beneficiary_crew = models.BooleanField(default=False)
    bank_account_name = models.CharField(max_length=255, null=True, blank=True)
    bank_account_number = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_transfer_beneficiary_relationship = models.CharField(
        max_length=255, null=True, blank=True
    )
    bank_transfer_beneficiary_contact = models.CharField(
        max_length=255, null=True, blank=True
    )
    bank_transfer_beneficiary_contact_platform = models.CharField(
        max_length=255, null=True, blank=True
    )
    has_deductions = models.BooleanField(default=False)
    deductions = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}, {self.start_date.strftime("%b %d, %Y")} - \
            {self.end_date.strftime("%b %d, %Y")}'
