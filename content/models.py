from django.db import models

from common.models import AuditableModel


class AggregatedContent(AuditableModel):
    content = models.JSONField(null=False)

    def __str__(self) -> str:
        return f"Aggregated content {self.created_at}"
