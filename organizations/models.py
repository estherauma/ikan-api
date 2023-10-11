from django.db import models
from common.models import AuditableModel


class Organization(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    logo = models.CharField(max_length=255, null=False, blank=False)
    status = models.CharField(max_length=255, null=False, blank=False)
    country = models.CharField(max_length=255, null=False, blank=False)
    city = models.CharField(max_length=255, null=False, blank=False)
    telephone = models.CharField(max_length=255, null=False, blank=False)
    email = models.CharField(max_length=255, null=False, blank=False)
    address_line_1 = models.CharField(max_length=255, null=False, blank=False)
    address_line_2 = models.CharField(max_length=255, null=False, blank=False)
    address_line_3 = models.CharField(max_length=255, null=False, blank=False)