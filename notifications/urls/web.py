from django.urls import path
from notifications.views.web import NotificationsView, NotificationDetailView, NotificationsDataView


app_name = 'notifications-web'

urlpatterns = [
    path('', NotificationsView.as_view(), name='notifications'),
    path('<pk>/', NotificationDetailView.as_view(), name='notification-details'),
    path('data', NotificationsDataView.as_view(), name='notifications-data'),
]
