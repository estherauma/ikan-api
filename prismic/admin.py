from django.contrib import admin
from .models import (
    AggregatedContent,
    PrismicWebhookNotificationsLog
    )
# Register your models here.
admin.site.register(AggregatedContent)
admin.site.register(PrismicWebhookNotificationsLog)
