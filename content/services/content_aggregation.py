import logging

from content.models import AggregatedContent
from content.services.aggregators import aggregate_documents
from content.services.strapi_content import StrapiContentService


logger = logging.getLogger(__name__)


class ContentAggregationService:
    def __init__(self, content_service=None):
        self.content_service = content_service or StrapiContentService()

    def aggregate_content(self, collection_name="ikans", params=None):
        request_params = dict(params or {})
        custom_type = request_params.get("custom_type")

        data = self.content_service.get_all_documents(
            collection_name=collection_name,
            params=request_params,
        )
        if data is None:
            logger.error("Aggregation aborted because no data was returned for collection %s", collection_name)
            return None

        documents = data.get("data", [])
        aggregated_data, aggregated_count = aggregate_documents(
            documents,
            self.content_service.base_url,
            custom_type=custom_type,
        )

        if custom_type:
            aggregated_data = self._merge_with_latest_snapshot(aggregated_data)

        snapshot = AggregatedContent.objects.create(content=aggregated_data)
        self._prune_old_snapshots()

        logger.info(
            "Saved aggregated content snapshot %s for collection %s%s with %s aggregated documents",
            snapshot.id,
            collection_name,
            f" and custom type {custom_type}" if custom_type else "",
            aggregated_count,
        )
        return snapshot, aggregated_count

    def _merge_with_latest_snapshot(self, partial_data):
        latest_snapshot = AggregatedContent.objects.order_by("-created_at").first()
        if latest_snapshot is None or latest_snapshot.content is None:
            return partial_data

        merged = {**latest_snapshot.content}
        for locale, locale_data in partial_data.items():
            merged[locale] = {
                **merged.get(locale, {}),
                **locale_data,
            }
        return merged

    def _prune_old_snapshots(self):
        snapshot_ids_to_delete = list(
            AggregatedContent.objects.order_by("-created_at").values_list("id", flat=True)[3:]
        )
        if snapshot_ids_to_delete:
            deleted_count, _ = AggregatedContent.objects.filter(id__in=snapshot_ids_to_delete).delete()
            logger.info("Pruned %s old aggregated content snapshot records", deleted_count)
