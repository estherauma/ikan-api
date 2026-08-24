from django.core.management import BaseCommand

from content.services import ContentAggregationService


class Command(BaseCommand):
    help = "Fetch content from Strapi and save an aggregated snapshot"

    def add_arguments(self, parser):
        parser.add_argument(
            "--collection",
            default="ikans",
            help="Strapi collection name to fetch. Defaults to 'ikans'.",
        )
        parser.add_argument(
            "--custom-type",
            default=None,
            help="Aggregate only one custom type and merge it into the latest snapshot.",
        )

    def handle(self, *args, **options):
        collection_name = options["collection"]
        custom_type = options["custom_type"]
        params = {}
        if custom_type:
            params["custom_type"] = custom_type

        result = ContentAggregationService().aggregate_content(
            collection_name=collection_name,
            params=params,
        )

        if result is None:
            self.stderr.write(
                self.style.ERROR(f"Content aggregation failed for collection '{collection_name}'.")
            )
            return

        snapshot, aggregated_count = result

        self.stdout.write(
            self.style.SUCCESS(
                f"Content aggregation succeeded for '{collection_name}'"
                f"{f' ({custom_type})' if custom_type else ''}. "
                f"Aggregated {aggregated_count} document(s). Snapshot ID: {snapshot.id}"
            )
        )
