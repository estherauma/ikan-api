from django.db import models
from common.models import AuditableModel


class Agent(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    contact_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=255)
    logo_url = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    town = models.CharField(max_length=255)
    building_name = models.CharField(max_length=255)
    road = models.CharField(max_length=255)
