from django.shortcuts import redirect
from django.urls import reverse
from threading import local
import json


_request_local = local()


def get_current_request():
    return getattr(_request_local, 'request', None)


class SelectLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        try:
            if not request.user.is_authenticated:
                return self.get_response(request)

            # if language isn't set, redirect to change language page
            if not request.session.get('language'):
                language_url = reverse('select_language')
                if request.path != language_url:
                    return redirect(language_url)

            return self.get_response(request)
        finally:
            _request_local.request = None


class LowercaseEmailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process requests that typically contain submission data
        if request.method in ['POST', 'PUT', 'PATCH']:

            # Post data
            if request.POST and 'email' in request.POST:
                # request.POST is immutable by default, so we copy it to modify it
                post_data = request.POST.copy()
                post_data['email'] = post_data['email'].strip().lower()
                request.POST = post_data

            # JSON API Data
            elif request.content_type == 'application/json' and request.body:
                try:
                    data = json.loads(request.body)
                    if isinstance(data, dict) and 'email' in data:
                        data['email'] = str(data['email']).strip().lower()
                        # Re-encode the modified dict back into the request body
                        request._body = json.dumps(data).encode('utf-8')
                except (json.JSONDecodeError, AttributeError):
                    pass  # Keep going if the JSON is malformed

        response = self.get_response(request)
        return response
