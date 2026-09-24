import logging
from datetime import timedelta

from django.utils import timezone

from content.models import AggregatedContent
from content.services.aggregators import aggregate_documents
from content.services.strapi_content import StrapiContentService


logger = logging.getLogger(__name__)
AGGREGATED_CONTENT_RETENTION_WINDOW = timedelta(days=1)


class ContentAggregationService:
    def __init__(self, content_service=None):
        self.content_service = content_service or StrapiContentService()

    def handle_publish_event(self, collection_name="ikans", payload=None):
        payload = payload or {}
        entry = payload.get("entry") or {}
        document_id = entry.get("id")
        latest_stored_content = self._get_latest_stored_content() or {}

        if document_id is None:
            logger.error("Publish webhook payload is missing entry.id for collection %s", collection_name)
            return None

        document_response = self.content_service.get_document(
            {
                "collection_name": collection_name,
                "document_id": document_id,
            }
        )
        if document_response is None:
            logger.error(
                "Failed to fetch Strapi document %s for collection %s",
                document_id,
                collection_name,
            )
            return None

        document = document_response.get("data")
        if document is None:
            logger.error(
                "Fetched Strapi document %s for collection %s but response had no document data",
                document_id,
                collection_name,
            )
            return None

        aggregated_data, aggregated_count = aggregate_documents(
            [document],
            existing_content=latest_stored_content,
        )
        if not aggregated_data:
            logger.error(
                "Aggregation produced no content for Strapi document %s in collection %s",
                document_id,
                collection_name,
            )
            return None

        merged_content = self._merge_with_latest_stored_content(
            aggregated_data,
            existing_content=latest_stored_content,
        )
        content_record = self._save_aggregated_content(merged_content)
        logger.info(
            "Saved aggregated content record %s after publish webhook for document %s in collection %s",
            content_record.id,
            document_id,
            collection_name,
        )
        return content_record, aggregated_count

    def handle_remove_event(self, collection_name="ikans", payload=None):
        payload = payload or {}
        entry = payload.get("entry") or {}
        page_key = entry.get("uid")
        locale = entry.get("locale")
        latest_stored_content = self._get_latest_stored_content()

        if not page_key or not locale:
            logger.error(
                "Remove webhook payload is missing uid or locale for collection %s: uid=%s locale=%s",
                collection_name,
                page_key,
                locale,
            )
            return None

        if latest_stored_content is None:
            logger.info(
                "No stored aggregated content exists while handling remove webhook for uid=%s locale=%s",
                page_key,
                locale,
            )
            return 0, 0

        updated_content, removed = self._remove_aggregated_entry(
            latest_stored_content,
            locale=locale,
            page_key=page_key,
        )
        if not removed:
            logger.info(
                "No aggregated entry found to remove for uid=%s locale=%s",
                page_key,
                locale,
            )
            return 0, 0

        content_record = self._save_aggregated_content(updated_content)
        logger.info(
            "Saved aggregated content record %s after remove webhook for uid=%s locale=%s",
            content_record.id,
            page_key,
            locale,
        )
        return content_record, 1

    def aggregate_content(self, collection_name="ikans", params=None):
        request_params = dict(params or {})
        custom_type = request_params.get("custom_type")
        latest_stored_content = self._get_latest_stored_content()

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
            custom_type=custom_type,
            existing_content=latest_stored_content,
        )

        if custom_type:
            aggregated_data = self._merge_with_latest_stored_content(
                aggregated_data,
                existing_content=latest_stored_content,
            )

        content_record = self._save_aggregated_content(aggregated_data)

        logger.info(
            "Saved aggregated content record %s for collection %s%s with %s aggregated documents",
            content_record.id,
            collection_name,
            f" and custom type {custom_type}" if custom_type else "",
            aggregated_count,
        )
        return content_record, aggregated_count

    def _save_aggregated_content(self, aggregated_data):
        latest_record = AggregatedContent.objects.order_by("-created_at").first()
        retention_cutoff = timezone.now() - AGGREGATED_CONTENT_RETENTION_WINDOW

        if latest_record and latest_record.created_at and latest_record.created_at >= retention_cutoff:
            latest_record.content = aggregated_data
            latest_record.save()
            content_record = latest_record
        else:
            content_record = AggregatedContent.objects.create(content=aggregated_data)

        self._delete_older_agg_content()
        return content_record

    def _merge_with_latest_stored_content(self, partial_data, existing_content=None):
        latest_stored_content = existing_content if existing_content is not None else self._get_latest_stored_content()

        if latest_stored_content is None:
            return partial_data

        merged = {**latest_stored_content}
        for locale, locale_data in partial_data.items():
            merged[locale] = {
                **merged.get(locale, {}),
                **locale_data,
            }
        return merged

    def _remove_aggregated_entry(self, existing_content, locale, page_key):
        updated_content = {**(existing_content or {})}
        locale_content = updated_content.get(locale)
        if not isinstance(locale_content, dict) or page_key not in locale_content:
            return updated_content, False

        updated_locale_content = {**locale_content}
        updated_locale_content.pop(page_key, None)
        if updated_locale_content:
            updated_content[locale] = updated_locale_content
        else:
            updated_content.pop(locale, None)
        return updated_content, True

    def _get_latest_stored_content(self):
        latest_record = AggregatedContent.objects.order_by("-created_at").first()
        if latest_record is None or latest_record.content is None:
            return None
        return latest_record.content

    def _delete_older_agg_content(self):
        retention_cutoff = timezone.now() - AGGREGATED_CONTENT_RETENTION_WINDOW
        deleted_count, _ = AggregatedContent.objects.filter(created_at__lt=retention_cutoff).delete()
        if deleted_count:
            logger.info("Deleted %s aggregated content records older than %s", deleted_count, retention_cutoff)
