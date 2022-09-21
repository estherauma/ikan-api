from django.shortcuts import render

from http import HTTPStatus

from prismic.models import AggregatedContent

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
