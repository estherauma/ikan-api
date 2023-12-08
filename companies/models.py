from django.db import models
from common.models import AuditableModel


class Company(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    description =   models.CharField(max_length=255, null=False, blank=False)
    logo_url = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    telephone = models.CharField(max_length=255)
    email = models.EmailField(unique=False)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255)
    address_line_3 = models.CharField(max_length=255)
    

    def __str__(self):
        return self.name