from asgiref.local import Local
from content.utils import ContentUtils


_request_state = Local()


PAGE_TRANSLATION_MAP = {
    'dashboard-overview': 'traders-dashboard',
    'dashboard-wage-payments': 'traders-dashboard',
}


class Translator:
    def __init__(self, request):
        self.request = request
        self._content_utils = None
        self._common_text = None
        self._page_text = {}
        self._form_text = {}

    @property
    def content_utils(self):
        if self._content_utils is None:
            self._content_utils = ContentUtils(self.request)
        return self._content_utils

    @property
    def common_text(self):
        return self._common_text_lookup()

    def t(self, key, scope=None, **kwargs):
        if not key:
            return ''

        source, source_name = self._parse_scope(scope)

        if source == 'common':
            value = self._common_text_lookup().get(key, key)
            return self._format_value(value, key, **kwargs)

        if source == 'form':
            value = self._form_text_lookup(source_name).get(key, key)
            return self._format_value(value, key, **kwargs)

        if source == 'page':
            value = self._page_text_lookup(source_name).get(key, key)
            return self._format_value(value, key, **kwargs)

        value = (
            self._page_text_lookup(source_name).get(key)
            or self._common_text_lookup().get(key)
            or self._form_text_lookup().get(key)
            or key
        )
        return self._format_value(value, key, **kwargs)

    def _parse_scope(self, scope):
        if not scope:
            return None, self._page_name()

        if ':' in scope:
            source, source_name = scope.split(':', 1)
            return source, source_name

        return scope, self._page_name()

    def _page_name(self):
        resolver_match = getattr(self.request, 'resolver_match', None)
        url_name = getattr(resolver_match, 'url_name', None)
        return PAGE_TRANSLATION_MAP.get(url_name)

    def _common_text_lookup(self):
        if self._common_text is None:
            self._common_text = self.content_utils.get_common_text() or {}
        return self._common_text

    def _page_text_lookup(self, page=None):
        page = page or self._page_name()
        if not page:
            return {}

        if page not in self._page_text:
            self._page_text[page] = self.content_utils.get_page_text(page) or {}
        return self._page_text[page]

    def _form_text_lookup(self, form=None):
        if not form:
            return {}

        if form not in self._form_text:
            form_text = {}
            form_questions = self.content_utils.get_form_questions(form) or []
            for question in form_questions:
                key = question.get('key')
                label = question.get('label')
                if key and label:
                    form_text[key] = label
            self._form_text[form] = form_text

        return self._form_text[form]

    def _format_value(self, value, key, **kwargs):
        if not kwargs:
            return value

        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return key


def set_current_request(request):
    _request_state.request = request


def get_current_request():
    return getattr(_request_state, 'request', None)


def clear_current_request():
    if hasattr(_request_state, 'request'):
        del _request_state.request
