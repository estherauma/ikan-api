from http import HTTPStatus

from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import AggregatedContent
from content.serializers import AggregatedContentSerializer


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
    def post(self, request):
        return Response(
            {
                "status": "FAIL",
                "data": [],
                "error_messages": ["Content sync is not implemented yet."],
            },
            HTTPStatus.NOT_IMPLEMENTED,
        )
