from django.utils.dateparse import parse_datetime
from http import HTTPStatus
from prismic.models import AggregatedContent, PrismicWebhookNotificationsLog
from prismic.fetch_data import (
    PrismicAPI,
    PrismicMessagingAPI,
    PrismicPushNotificationAPI,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import (
    AggregatedContentSerializer,
    MessageContentSerializer,
    PushNotificationsContentSerializer,
)
from decouple import config
import requests


class AggregatedContentView(APIView):
    def get(self, request):
        latest = AggregatedContent.objects.order_by('-created_at')[:1].get()
        serializer = AggregatedContentSerializer(latest, many=False)
        return Response({
            'status': 'OK',
            'data': [serializer.data],
            'error_messages': []
        }, HTTPStatus.OK)


class UpdatedContentView(APIView):
    def post(self, request):
        data = request.data
        # Save webhook notification data for troubleshooting purposes
        log = PrismicWebhookNotificationsLog()
        log.content = data
        log.save()

        # TODO use the notification object  master ref to fetch new updated contnet
        # Right now, just fetch and aggregate all content.
        PrismicAPI()

        return Response({
            'status': 'OK',
            'data': [],
            'error_messages': []
        }, HTTPStatus.OK)


@api_view(['GET'])
def compare_content(request):
    app_content_created_at = request.query_params.get('app_content_created_at')
    parsed_app_content_created_at = parse_datetime(app_content_created_at)
    latest_content = AggregatedContent.objects.order_by('-created_at')[:1].get()
    serializer = AggregatedContentSerializer(latest_content, many=False)
    latest_content_created_at = parse_datetime(serializer.data['created_at'])
    if latest_content_created_at == parsed_app_content_created_at:
        return Response({
            'status': 'OK',
            'data': "",
            'new': False,
            'error_messages': []
        }, status=HTTPStatus.OK)
    else:
        return Response({
            'status': 'OK',
            'data': [serializer.data],
            'new': True,
            'error_messages': []
        }, status=HTTPStatus.OK)


class MessagingWebhookView(APIView):

    def post(self, request):
        access_token = request.headers.get('token')
        domain = request.data.get('domain')
        docs = request.data.get('documents')
        doc_id = docs[0]
        if access_token is None:
            return Response({'status': 'FAIL'}, HTTPStatus.UNAUTHORIZED)

        messaging_content = PrismicMessagingAPI(request, access_token)
        hook_data = None

        try:
            hook_data = messaging_content.get_published_content()
        except Exception as e:
            print(e)

            return Response({
                'status': 'FAIL',
                'error': 'Internal server error'
            }, HTTPStatus.INTERNAL_SERVER_ERROR)

        serializer = MessageContentSerializer(
            data=hook_data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # publish message
            aggregated_content = hook_data.get('aggregated_content')

            # TODO: Refactor this code to use selected language
            stop_execution = False
            for lang in aggregated_content:
                lang_data = aggregated_content.get(lang)
                for item, value in lang_data.items():
                    if value['id'] == doc_id:
                        message = value
                        message['domain'] = domain
                        self.publish_notification(message)
                        stop_execution = True
                        break
                if stop_execution:
                    break

            return Response(
                {
                    "status": "OK",
                    "data": serializer.data,
                },
                HTTPStatus.OK,
            )
        else:
            return Response(
                {"status": "FAIL", "data": [], "errors": serializer.errors},
                HTTPStatus.BAD_REQUEST,
            )

    def get_push_notifications_base_url(self):
        environment = config('ENVIRONMENT')

        if environment == 'Development' or environment == 'development':
            return config('JGW_DEV_PUSH_NOTIFICATION_API')
        elif environment == 'Staging' or environment == 'staging':
            return config('JGW_STAGING_PUSH_NOTIFICATION_API')
        elif environment == 'Production' or environment == 'production':
            return config('JGW_PROD_PUSH_NOTIFICATION_API')

        return None

    def publish_notification(self, message):
        base_url = self.get_push_notifications_base_url()
        if base_url is None:
            return Response({
                'status': 'FAIL',
                'message': 'No push notifications url provided'
            }, HTTPStatus.BAD_REQUEST)

        # Logic push notification server needs to be updated to cater for the message format
        # that will be sent from the tuna-messaging webhook from prismic
        # Currently works for triggers from prismic push notification webhook
        url = f'{base_url}tuna/v1/message-notification'

        try:
            response = requests.post(url, json=message)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print(f"Could not publish notification. {error}")


class PushNotificationWebhookView(APIView):
    def post(self, request):
        access_token = request.headers.get("token")
        domain = request.data.get("domain")
        docs = request.data.get("documents")
        doc_id = docs[0]

        notif_content = PrismicPushNotificationAPI(request, access_token)
        hook_data = None

        try:
            hook_data = notif_content.get_published_notif_content()
        except Exception as e:
            print(e)

            return Response(
                {"status": "FAIL", "error": "Internal server error"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        serializer = PushNotificationsContentSerializer(data=hook_data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # publish notification
            aggregated_notif_content = hook_data.get("aggregated_content")

            stop_execution = False
            for lang in aggregated_notif_content:
                lang_data = aggregated_notif_content.get(lang)
                for item, value in lang_data.items():
                    if value["id"] == doc_id:
                        notif_obj = value["notifData"]
                        notif_obj["domain"] = domain
                        self.publish_push_notification(notif_obj)
                        stop_execution = True
                        break
                if stop_execution:
                    break
            return Response(
                {
                    "status": "OK",
                    "data": serializer.data,
                },
                HTTPStatus.OK,
            )
        else:
            return Response(
                {"status": "FAIL", "data": [], "errors": serializer.errors},
                HTTPStatus.BAD_REQUEST,
            )

    def get_push_notifications_base_url(self):
        environment = config("ENVIRONMENT")

        if environment == "Development" or environment == "development":
            return config("JGW_DEV_PUSH_NOTIFICATION_API")
        elif environment == "Staging" or environment == "staging":
            return config("JGW_STAGING_PUSH_NOTIFICATION_API")
        elif environment == "Production" or environment == "production":
            return config("JGW_PROD_PUSH_NOTIFICATION_API")

        return None

    def publish_push_notification(self, notif_obj):
        base_url = self.get_push_notifications_base_url()
        if base_url is None:
            return Response(
                {"status": "FAIL", "message": "No push notifications url provided"},
                HTTPStatus.BAD_REQUEST,
            )

        url = f"{base_url}tuna/v1/message-notification"

        try:
            response = requests.post(url, json=notif_obj)

            return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as error:
            print(f"Could not publish notification. {error}")
            return Response(
                {"status": "FAIL", "message": "Could not publish push notification"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            print(f"An error ccurred. {e}")
            return Response(
                {"status": "FAIL", "message": "Unexpected server error"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
