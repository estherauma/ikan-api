from accounts.models import User
from common.models import AuditableModel
from django.db import models
from vessels.models import Vessel


def wage_upload_path(instance, filename):
    return f'wages/{instance.user.id}_ikan_{filename}'


class Wage(AuditableModel):
    RIGHT_AMOUNT_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unsure', 'Unsure'),
    ]
    BENEFICIARY_RELATIONSHIP_CHOICES = [
        ('self', 'Crew member himself'),
        ('family_or_friend', 'Family/friend'),
        ('crew_member_and_family_or_friend', 'Crew member and family/friend'),
    ]
    STATUS_CHOICES = [
        ('action_required', 'Action Required'),
        ('issue_pending', 'Issue Pending'),
        ('received', 'Received'),
    ]

    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payslip = models.FileField(upload_to=wage_upload_path, null=True, blank=True)
    crew_bank_transfer_receipt = models.FileField(upload_to=wage_upload_path, null=True, blank=True)
    beneficiary_bank_transfer_receipt = models.FileField(upload_to=wage_upload_path, null=True, blank=True)
    beneficiary_relationship = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_contact = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_contact_platform = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=30, default='action_required', choices=STATUS_CHOICES)
    crew_received_right_amount = models.CharField(max_length=10, choices=RIGHT_AMOUNT_CHOICES, null=True, blank=True)
    beneficiary_received_right_amount = models.CharField(max_length=10,
                                                         choices=RIGHT_AMOUNT_CHOICES, null=True, blank=True)

    @property
    def duration(self):
        if self.start_date and self.end_date:
            years = self.end_date.year - self.start_date.year
            months = self.end_date.month - self.start_date.month
            total_months = (years * 12) + months + 1
            if total_months < 0:
                total_months = 0
            return total_months
        return None

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}, {self.start_date.strftime("%b %d, %Y")} - \
            {self.end_date.strftime("%b %d, %Y")}'
