from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from datetime import datetime
from http import HTTPStatus

from prismic.models import AggregatedContent

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from .serializers import AggregatedContentSerializer
class AggregatedContentView(APIView):
    def get(self, request):
        data = AggregatedContent.objects.reverse()
        # Order and put the latest aggregated object on top 
        # Mobile app picks the first object
        latest = data[::-1]
        serializer = AggregatedContentSerializer(latest, many=True)
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'error_messages': []
        }, HTTPStatus.OK)


@api_view(['GET'])
def compare_content(request):
    app_content_created_at = request.GET['app_content_created_at']
    parsed_app_content_created_at = parse_datetime(app_content_created_at)

    data = AggregatedContent.objects.reverse()
    latest = data[::-1]
    serializer = AggregatedContentSerializer(latest, many=True)
    lastets_content_created_at = parse_datetime(
        serializer.data[0]['created_at']
    )

    if lastets_content_created_at == parsed_app_content_created_at:
        return Response({
            'status': 'OK',
            'data': "",
            'new': False,
            'error_messages': []
        }, HTTPStatus.OK)
    else:
        return Response({
            'status': 'OK',
            'data': serializer.data,
            'new': True,
            'error_messages': []
        }, HTTPStatus.OK)
