from django.contrib import admin
from .models import (
    AggregatedContent,
    PrismicWebhookNotificationsLog,
    MessagingContent,
    PushNotificationsContent
)


# Register your models here.
admin.site.register(AggregatedContent)
admin.site.register(PrismicWebhookNotificationsLog)
admin.site.register(MessagingContent)
admin.site.register(PushNotificationsContent)
