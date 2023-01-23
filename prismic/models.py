from contextlib import nullcontext
from django.db import models
from common.models import AuditableModel
# Create your models here.

class AggregatedContent(AuditableModel):
    content = models.JSONField(null=False)

    def __str__(self) -> str:
        return f'Aggregated %s' % self.created_at

class PrismicWebhookNotificationsLog(AuditableModel):
    content  = models.JSONField(null=True)
    
    def __str__(self) -> str:
        return f'%s Notifications Log' % self.created_at
