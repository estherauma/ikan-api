from django.shortcuts import render

from http import HTTPStatus

from prismic.models import (AggregatedContent, PrismicWebhookNotificationsLog)
from prismic.fetch_data import PrismicAPI

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class UpdatedContentView(APIView):
    def post(self, request):
        data = request.data
        # Save webhook notification data for troubleshooting purposes
        log = PrismicWebhookNotificationsLog()
        log.content = data
        log.save()
        
        # TODO use the notification object  master ref to fetch new updated contnet
        # Right now, just fetch and aggregate all content. 
        content = PrismicAPI()
        
        return Response({
            'status': 'OK',
            'data': [],
            'error_messages': []
        }, HTTPStatus.NO_CONTENT)
