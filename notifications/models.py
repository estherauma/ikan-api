from django.db import models
from common.models import AuditableModel
from accounts.models import User
from common.utils import generate_uuid


class Notification(AuditableModel):
    app_ref = models.CharField(max_length=40, default=generate_uuid, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=255, default='general')
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=255)
    is_displayed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        if self.user.name_on_contract:
            return f"Notification for {self.user.name_on_contract} - {self.title}"
        return f"Notification for {self.user.first_name} {self.user.last_name} - {self.title}"
