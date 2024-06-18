from django.db import models
from common.models import AuditableModel


class Vessel(AuditableModel):
    app_ref = models.CharField(max_length=255, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    reg_no = models.CharField(max_length=255, null=False, blank=False)
    vessel_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    capacity = models.CharField(max_length=255, null=True, blank=True)
    commissioning_date = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name} - {self.reg_no}'


class VesselImage(AuditableModel):
    app_ref = models.CharField(max_length=255, null=False, blank=False)
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='vessel_image')
    image_url = models.CharField(max_length=255, null=False, blank=False)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.vessel.name} - {self.image_url}'
