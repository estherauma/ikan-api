from content.services.aggregation_utils import (
    aggregate_additional_text,
    aggregate_common_text_entries,
    aggregate_image,
    aggregate_media,
    aggregate_rich_text,
    aggregate_text_area,
    aggregate_text,
    aggregate_tutorials,
    empty_media,
)


def aggregate_documents(documents, base_url, custom_type=None):
    aggregated_data = {}
    aggregated_count = 0

    for item in documents:
        item_custom_type = item.get("custom_type")
        if custom_type and item_custom_type != custom_type:
            continue

        aggregator = AGGREGATORS.get(item_custom_type)
        if not aggregator:
            continue

        page_key, locale, page_data = aggregator(item, base_url)
        if not locale or not page_key or not page_data:
            continue

        if locale not in aggregated_data:
            aggregated_data[locale] = {}

        aggregated_data[locale][page_key] = page_data
        aggregated_count += 1

    return aggregated_data, aggregated_count


def aggregate_app_tutorials(item, base_url):
    if item.get("uid") != "app-tutorials":
        return None, None, None

    locale = item.get("locale")
    dynamic_zone = item.get("dynamic_zone", [])

    return (
        "app-tutorials",
        locale,
        {
            "id": item.get("id"),
            "page_name": "app-tutorials",
            "tutorials": aggregate_tutorials(dynamic_zone, base_url),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "welcome_text": aggregate_text(item.get("welcome_text")),
            "welcome_audio": empty_media(),
            "welcome_title": item.get("page_title"),
            "welcome_video": aggregate_media(item.get("welcome_video"), base_url),
            "additional_text": aggregate_additional_text(dynamic_zone),
            "analyticsEventName": item.get("analytics_event_name"),
            "welcome_video_for_public": aggregate_media(item.get("welcome_video_for_public"), base_url),
        },
    )


def aggregate_case_study(item, base_url):
    page_content = []
    description = []

    for zone in item.get("dynamic_zone", []):
        if zone.get("__component") != "ikan.text-area":
            continue

        text_area = aggregate_text_area(zone)
        if text_area["description"] and not description:
            description = text_area["description"]
        page_content.append(text_area)

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "uid": item.get("uid"),
            "id": item.get("id"),
            "type": "case_study",
            "image": aggregate_image(item.get("cover_image"), base_url),
            "language": item.get("locale"),
            "pageIcon": aggregate_image(item.get("page_icon"), base_url),
            "pageTitle": item.get("page_title"),
            "subChapter": None,
            "description": description,
            "pageContent": page_content,
            "pageTitleAudio": {},
            "analyticsEventName": item.get("analytics_event_name"),
        },
    )


def aggregate_common_text(item, _base_url):
    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "data": aggregate_common_text_entries(item.get("dynamic_zone", [])),
        },
    )


AGGREGATORS = {
    "app_tutorials": aggregate_app_tutorials,
    "case_study": aggregate_case_study,
    "common_text": aggregate_common_text,
}
