# from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from datetime import datetime
from http import HTTPStatus
from prismic.models import (
    AggregatedContent,
    MessagingContent,
    PrismicWebhookNotificationsLog
)
from prismic.fetch_data import PrismicAPI, PrismicMessagingAPI
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


class MessagingWebhookView(APIView):
    def get_messaging_repo_content(self, content):
        try:
            print('reaching........')
            return MessagingContent.objects.get(content=content)
        except MessagingContent.DoesNotExist:
            return None

    def post(self, request):
        print('Payload................', request.data)
        access_token = request.headers.get('token')
        if access_token is None:
            return Response({'status': 'FAIL'}, HTTPStatus.UNAUTHORIZED)
        # check this
        saved_content = self.get_messaging_repo_content(request.data.get('content'))
        print('saved_content......', saved_content)
        # if saved_content is None:
        #     print('nnnnnnnnnnnnnnnnnn..........')
        #     return Response({'status': 'FAIL'}, HTTPStatus.NOT_FOUND)

        messaging_content = PrismicMessagingAPI(
            request, access_token, saved_content)
        hook_data = None

        try:
            print('hook_data......mssgg....before......', hook_data)
            hook_data = messaging_content.get_published_content()
            print('hook_data......mssgg......after.....', hook_data)
            print('''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''')
        except Exception as e:
            # remote_error_handler(e) // look into this
            # log error
            # capture_exception(e)
            print(e)

            return Response({
                'status': 'FAIL',
                'error': 'Internal server error'
            }, HTTPStatus.INTERNAL_SERVER_ERROR)

        # serializer = PrismicRepoSerializer(
        #     repo_db_content, data=hook_data, partial=True)

        # if serializer.is_valid():
        #     serializer.save()
        #     return Response({
        #         'status': 'OK',
        #         'data': serializer.data,
        #     }, HTTPStatus.OK)
        # else:
        #     return Response({
        #         'status': 'FAIL',
        #         'data': [],
        #         'errors': serializer.errors
        #     }, HTTPStatus.BAD_REQUEST)
