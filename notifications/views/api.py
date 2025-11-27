from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime


class NotificationApiListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class NotificationDetailApiView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_notification(self, id):
        try:
            return Notification.objects.get(id=id)
        except Notification.DoesNotExist:
            return Response(
                {
                    'status': 'FAIL',
                    'message': 'Notification not found.'
                },
                status.HTTP_404_NOT_FOUND
            )

    def retrieve(self, request, id):
        notification = self.get_notification(id)
        serializer = self.serializer_class(notification)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, id):
        notification = self.get_notification(id)
        req_updated_at = request.data.get('updated_at', None)
        req_updated_at = parse_datetime(req_updated_at) if req_updated_at else None
        if req_updated_at is None or req_updated_at > notification.updated_at:
            serializer = self.serializer_class(
                notification, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user.id)
            return Response({
                'status': 'OK',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'OK',
                'message': 'Record is already up to date, no changes made.'
            }, status=status.HTTP_200_OK)

    def destroy(self, request, id):
        notification = self.get_notification(id)
        notification.delete()
        return Response({
            'status': 'OK',
            'message': 'Notification deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)
