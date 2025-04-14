from notifications.models import Notification


def create_notification(user, title, message, status, metadata=None):

    notification = Notification.objects.create(
        user=user, title=title, message=message, status=status, metadata=metadata
    )
    return notification
