from django.db import models
from common.models import AuditableModel
from accounts.models import User


class Notification(AuditableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=255, default='general')
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=255)
    is_displayed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    meta = models.JSONField(default=dict, null=True, blank=True)
