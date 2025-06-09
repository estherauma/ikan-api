from prismic.models import AggregatedContent


class PrismicUtils:
    def __init__(self, request):
        self.user = request.user
        self.is_superuser = self.user.is_superuser
        # TODO: use selected language after implementing localization
        self.language = 'en-us'
        self.aggregated_content = None

    def get_content(self):
        all_data = AggregatedContent.objects.all()
        recent_data = all_data.order_by('-created_at').first()
        if recent_data and recent_data.content:
            return recent_data.content[self.language]
        return None

    def get_content_by_property_name(self, property_name):
        content = self.get_content()
        if content and property_name in content:
            return content[property_name]
        return None
