from django.urls import path

from prismic.views import (
    AggregatedContentView,
    compare_content,
    UpdatedContentView,
    MessagingWebhookView,
    PushNotificationWebhookView
)

urlpatterns = [
    path('aggregated/', AggregatedContentView.as_view(), name='aggregated-content'),
    path('compare/', compare_content, name="compare_content"),
    path('updated', UpdatedContentView.as_view(), name='updated-content'),
    path('messaging', MessagingWebhookView.as_view(), name='messaging-webhook'),
    path('push-notifications', PushNotificationWebhookView.as_view(), name='push-notifications-webhook')
]
