from django.shortcuts import redirect
from django.urls import reverse


class SelectLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # if language isn't set, redirect to change language page
        if not request.session.get('language'):
            language_url = reverse('select_language')
            if request.path != language_url:
                return redirect(language_url)

        return self.get_response(request)
