from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from notifications.models import Notification
from django.http import JsonResponse


class NotificationsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'home.html')


class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'detail.html'
    context_object_name = 'notification'


class NotificationsDataView(LoginRequiredMixin, View):
    def get(self, request):
        super_user = self.request.user.is_superuser
        notifications = Notification.objects.all() if super_user else Notification.objects.filter(user=request.user)
        notifications_list = []
        for notification in notifications:
            notification = {
                "id": notification.id,
                "app_ref": notification.app_ref,
                "user": notification.user,
                "title": notification.title,
                "message": notification.message,
                "status": notification.status,
                # "metadata": notification.metadata,
                "is_displayed": notification.is_displayed,
                "is_deleted": notification.is_deleted,
                "created_at": notification.created_at,
                "created_by": notification.created_by_id,
                "updated_at": notification.updated_at,
                "updated_by": notification.updated_by_id,
                "deleted_at": notification.deleted_at,
                "deleted_by": notification.deleted_by_id,
                "actions": "<a href='/notifications/" + str(notification.id) +
                           "' class='btn btn-primary btn-sm'><i class='mdi mdi-eye'></i> View</a>"
            }
            notifications_list.append(notification)
        return JsonResponse(notifications_list, safe=False)
