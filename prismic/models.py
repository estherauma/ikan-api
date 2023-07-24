from django.db import models
from common.models import AuditableModel
# Create your models here.


class AggregatedContent(AuditableModel):
    content = models.JSONField(null=False)

    def __str__(self) -> str:
        return f'Aggregated  {self.created_at}'


class PrismicWebhookNotificationsLog(AuditableModel):
    content = models.JSONField(null=True)

    def __str__(self) -> str:
        return f' Notifications Log {self.created_at}'


class MessagingContent(AuditableModel):
    content = models.JSONField(blank=True, null=True)
    aggregated_content = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return f'Messaging Content. Last updated on {self.updated_at}'
