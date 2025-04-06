from django.urls import path
from notifications.views.api import NotificationApiListView, NotificationDetailApiView


app_name = 'notifications'

urlpatterns = [
    path('notifications', NotificationApiListView.as_view(), name='notification-list'),
    path('notifications/<str:id>', NotificationDetailApiView.as_view(), name='notification-detail'),
]
