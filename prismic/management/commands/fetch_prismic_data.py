from django.core.management import BaseCommand
from prismic.fetch_data import PrismicAPI


class Command(BaseCommand):
    help = 'Interact with the prismic API'

    def handle(self, *args, **options):
        data = PrismicAPI()
        x = data.build_url(type='doc_search')

        # TODO: fetch messaging content
