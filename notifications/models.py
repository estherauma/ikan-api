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
    metadata = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.first_name} {self.user.last_name} - {self.title}"
