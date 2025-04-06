from notifications.models import Notification


def create_notification(user, title, message, status, meta=None):
    if meta is None:
        meta = {}

    notification = Notification.objects.create(
        user=user, title=title, message=message, status=status, meta=meta
    )
    return notification
