import logging
from http import HTTPStatus

from decouple import config
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import AggregatedContent
from content.serializers import AggregatedContentSerializer
from content.services import ContentAggregationService


logger = logging.getLogger(__name__)


class AggregatedContentView(APIView):
    def get(self, request):
        latest = AggregatedContent.objects.order_by("-created_at").first()
        if latest is None:
            return Response(
                {
                    "status": "OK",
                    "data": [],
                    "error_messages": [],
                },
                HTTPStatus.OK,
            )

        serializer = AggregatedContentSerializer(latest, many=False)
        return Response(
            {
                "status": "OK",
                "data": [serializer.data],
                "error_messages": [],
            },
            HTTPStatus.OK,
        )


@api_view(["GET"])
def compare_content(request):
    app_content_created_at = request.query_params.get("app_content_created_at")
    parsed_app_content_created_at = parse_datetime(app_content_created_at)
    latest_content = AggregatedContent.objects.order_by("-created_at").first()

    if latest_content is None:
        return Response(
            {
                "status": "OK",
                "data": "",
                "new": False,
                "error_messages": [],
            },
            status=HTTPStatus.OK,
        )

    serializer = AggregatedContentSerializer(latest_content, many=False)
    latest_content_created_at = parse_datetime(serializer.data["created_at"])

    if latest_content_created_at == parsed_app_content_created_at:
        return Response(
            {
                "status": "OK",
                "data": "",
                "new": False,
                "error_messages": [],
            },
            status=HTTPStatus.OK,
        )

    return Response(
        {
            "status": "OK",
            "data": [serializer.data],
            "new": True,
            "error_messages": [],
        },
        status=HTTPStatus.OK,
    )


class UpdatedContentView(APIView):
    STRAPI_WEBHOOK_API_KEY = config("STRAPI_WEBHOOK_API_KEY", default=None)

    authentication_classes = []
    permission_classes = [AllowAny]
    supported_models = {
        'ikan': {
            'collection_name': "ikans",
        }
    }

    def post(self, request):
        if not self.STRAPI_WEBHOOK_API_KEY:
            logger.error("Strapi webhook API key is not configured.")
            return Response(
                {
                    "status": "FAIL",
                    "data": [],
                    "error_messages": ["Webhook API key is not configured."],
                },
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        provided_api_key = request.headers.get("X-API-Key")
        if provided_api_key != self.STRAPI_WEBHOOK_API_KEY:
            logger.error("Rejected Strapi webhook request due to invalid X-API-Key header.")
            return Response(
                {
                    "status": "FAIL",
                    "data": [],
                    "error_messages": ["Invalid webhook API key."],
                },
                HTTPStatus.FORBIDDEN,
            )

        logger.info("Received Strapi webhook payload: %s", request.data)
        model = request.data.get("model")
        event = request.data.get("event")
        entry = request.data.get("entry", {})
        model_config = self.supported_models.get(model)
        if not model_config:
            # ignore
            
            return Response(
                {
                    "status": "OK",
                    "data": [],
                    "error_messages": [],
                },
                HTTPStatus.OK,
            )
        collection_name = model_config["collection_name"]

        aggregation_service = ContentAggregationService()
        event_handlers = {
            "entry.publish": aggregation_service.handle_publish_event,
            "entry.delete": aggregation_service.handle_remove_event,
            "entry.unpublish": aggregation_service.handle_remove_event,
        }

        handler = event_handlers.get(event)
        if handler:
            result = handler(collection_name=collection_name, payload=request.data)
            if result is None:
                logger.error(
                    "Failed to sync content for model=%s event=%s entry_id=%s",
                    model,
                    event,
                    entry.get("id"),
                )
                return Response(
                    {
                        "status": "FAIL",
                        "data": [],
                        "error_messages": ["Failed to sync content."],
                    },
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            logger.info(
                "Synced content for model=%s event=%s entry_id=%s",
                model,
                event,
                entry.get("id"),
            )
            return Response(
                {
                    "status": "OK",
                    "data": [],
                    "error_messages": [],
                },
                HTTPStatus.OK,
            )

        logger.warning("Ignoring unsupported Strapi webhook event=%s for model=%s", event, model)
        return Response(
            {
                "status": "OK",
                "data": [],
                "error_messages": [],
            },
            HTTPStatus.OK,
        )
