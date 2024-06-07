from django.db import models
from common.models import AuditableModel
from accounts.models import User


class Document(AuditableModel):
    app_ref = models.CharField(max_length=255, null=False, blank=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=255, null=False, blank=False)
    file_url = models.CharField(max_length=255, null=False, blank=False)
    file_size = models.CharField(max_length=255, null=True, blank=True)
    doc_type = models.CharField(max_length=255, null=False, blank=False)
    is_essential = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.file_name} - {self.file_url}'


class Passport(AuditableModel):
    app_ref = models.CharField(max_length=255, null=False, blank=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passports')
    first_name = models.CharField(max_length=255, null=False, blank=False)
    surname = models.CharField(max_length=255, null=True, blank=True)
    passport_number = models.CharField(max_length=255, null=False, blank=False)
    date_of_issue = models.DateField(null=False, blank=False)
    date_of_expiry = models.DateField(null=False, blank=False)
    image_url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.surname} - {self.passport_number}'
