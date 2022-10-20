from contextlib import nullcontext
from django.db import models
from common.models import AuditableModel
# Create your models here.

class AggregatedContent(AuditableModel):
    content = models.JSONField(null=False)

class PrismicWebhookNotificationsLog(AuditableModel):
    content  = models.JSONField(null=True)
