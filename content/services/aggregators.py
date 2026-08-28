from decouple import config

from content.services.aggregation_utils import (
    DYNAMIC_ZONE_COMPONENT_AGGREGATORS,
    aggregate_form_question_component,
    aggregate_image,
    aggregate_media,
    aggregate_rich_text,
    aggregate_text,
    aggregate_media_reference,
    aggregate_additional_text_component,
    empty_media,
)


def aggregate_dynamic_zone(dynamic_zone, **context):
    return [entry["data"] for entry in aggregate_dynamic_zone_entries(dynamic_zone, **context)]


def aggregate_dynamic_zone_entries(dynamic_zone, **context):
    aggregated_components = []

    for component in dynamic_zone or []:
        component_name = component.get("__component")
        aggregator = DYNAMIC_ZONE_COMPONENT_AGGREGATORS.get(component_name)
        if not aggregator:
            continue

        aggregated_component = aggregator(component, **context)
        if aggregated_component is not None:
            # subtopic_id is unique to learning_hub_subchapter componennts, we can add it here
            if component.get("subtopic_id"):
                aggregated_component["subtopicId"] = component.get("subtopic_id")
            aggregated_components.append(
                {
                    "component": component_name,
                    "data": aggregated_component,
                }
            )

    return aggregated_components


def aggregate_documents(documents, custom_type=None, existing_content=None):
    aggregated_data = {}
    aggregated_count = 0
    base_url = config("STRAPI_BASE_URL").rstrip("/")
    aggregation_context = {
        "base_url": base_url,
        "existing_content": existing_content,
    }

    for item in documents:
        item_custom_type = item.get("custom_type")
        if custom_type and item_custom_type != custom_type:
            continue

        aggregator = CUSTOM_TYPE_AGGREGATORS.get(item_custom_type)
        if not aggregator:
            continue

        page_key, locale, page_data = aggregator(item, **aggregation_context)
        if not locale or not page_key or not page_data:
            continue

        if locale not in aggregated_data:
            aggregated_data[locale] = {}

        aggregated_data[locale][page_key] = page_data
        aggregated_count += 1

    return aggregated_data, aggregated_count


def aggregate_app_tutorials(item, **context):
    if item.get("uid") != "app-tutorials":
        return None, None, None

    base_url = context.get("base_url")
    locale = item.get("locale")
    dynamic_zone_entries = aggregate_dynamic_zone_entries(
        item.get("dynamic_zone", []),
        base_url=base_url,
    )
    tutorials = next(
        (entry["data"] for entry in dynamic_zone_entries if entry["component"] == "ikan.tutorials"),
        None,
    )
    additional_text = next(
        (entry["data"] for entry in dynamic_zone_entries if entry["component"] == "ikan.additional-text"),
        None,
    )

    return (
        "app-tutorials",
        locale,
        {
            "id": item.get("id"),
            "page_name": "app-tutorials",
            "tutorials": tutorials,
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "welcome_text": aggregate_text(item.get("welcome_text")),
            "welcome_audio": aggregate_media(item.get("welcome_audio"), base_url) or empty_media(),
            "welcome_title": item.get("page_title"),
            "welcome_video": aggregate_media(item.get("welcome_video"), base_url),
            "additional_text": additional_text,
            "analyticsEventName": item.get("analytics_event_name"),
            "welcome_video_for_public": (
                aggregate_media(item.get("welcome_video_for_public"), base_url) or empty_media()
            ),
        },
    )


def build_case_study_payload(item, base_url, sub_chapter=None):
    page_content = aggregate_dynamic_zone(
        item.get("dynamic_zone", []),
        base_url=base_url,
        include_audio=False,
    )
    description = []
    for content_block in page_content:
        if content_block.get("description"):
            description = content_block["description"]
            break

    return {
        "uid": item.get("uid"),
        "id": item.get("id"),
        "type": "case_study",
        "image": aggregate_image(item.get("cover_image") or item.get("page_icon"), base_url),
        "language": item.get("locale"),
        "pageIcon": aggregate_image(item.get("page_icon"), base_url),
        "pageTitle": item.get("page_title"),
        "subChapter": sub_chapter,
        "description": description,
        "pageContent": page_content,
        "pageTitleAudio": {},
        "analyticsEventName": item.get("analytics_event_name"),
    }


def aggregate_case_study(item, **context):
    base_url = context.get("base_url")
    return (
        item.get("uid"),
        item.get("locale"),
        build_case_study_payload(item, base_url),
    )


def aggregate_common_text(item, **context):
    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "data": aggregate_dynamic_zone(item.get("dynamic_zone", [])),
        },
    )


def aggregate_language_text(item, **context):
    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "data": aggregate_dynamic_zone(item.get("dynamic_zone", [])),
        },
    )


def aggregate_menu_content(item, **context):
    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at"),
            "data": aggregate_dynamic_zone(item.get("dynamic_zone", [])),
        },
    )


def aggregate_page(item, **context):
    base_url = context.get("base_url")
    dynamic_zone_entries = aggregate_dynamic_zone_entries(
        item.get("dynamic_zone", []),
        base_url=base_url,
    )
    page_media = {}
    additional_text = []

    for entry in dynamic_zone_entries:
        if entry["component"] == "ikan.media":
            media_key = entry["data"].get("media_key")
            media_value = entry["data"].get("media_value")
            if media_key and media_value:
                page_media[media_key] = media_value
        elif entry["component"] == "ikan.additional-text":
            additional_text = entry["data"]

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "additional_text": additional_text,
            "page_media": page_media,
        },
    )


def aggregate_form_questions(item, **context):
    form_questions = []
    additional_text = []

    for component in item.get("dynamic_zone", []):
        component_name = component.get("__component")
        if component_name == "ikan.form-question":
            form_questions.append(aggregate_form_question_component(component))
        elif component_name == "ikan.additional-text":
            additional_text = aggregate_additional_text_component(component)

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "page_name": item.get("uid"),
            "page_title": item.get("page_title"),
            "last_updated": item.get("last_published_at") or item.get("updatedAt"),
            "form_questions": form_questions,
            "additional_text": additional_text,
        },
    )


def aggregate_create_content_area(item, **context):
    base_url = context.get("base_url")
    existing_content = context.get("existing_content")
    page_content = aggregate_dynamic_zone(
        item.get("dynamic_zone", []),
        base_url=base_url,
        existing_content=existing_content or {},
        parent_uid=item.get("uid"),
        locale=item.get("locale"),
    )

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "id": item.get("id"),
            "type": "create_content_area",
            "language": item.get("locale"),
            "pageIcon": aggregate_image(item.get("page_icon"), base_url),
            "pageAudio": aggregate_media_reference(item.get("page_audio"), base_url) or empty_media(),
            "pageTitle": item.get("page_title") or "Title",
            "pageVideo": aggregate_media_reference(item.get("page_video"), base_url) or empty_media(),
            "page_name": item.get("uid"),
            "pageContent": page_content,
            "disclaimerText": item.get("disclaimer_text"),
            "pageTitleAudio": aggregate_media_reference(item.get("title_audio"), base_url) or {},
            "pageDescription": aggregate_rich_text(item.get("page_description")),
            "analyticsEventName": item.get("analytics_event_name"),
        },
    )


def aggregate_learning_hub_subchapter(item, **context):
    base_url = context.get("base_url")
    existing_content = context.get("existing_content")
    dynamic_zone_entries = aggregate_dynamic_zone_entries(
        item.get("dynamic_zone", []),
        base_url=base_url,
        existing_content=existing_content or {},
        parent_uid=item.get("uid"),
        locale=item.get("locale"),
    )
    subchapter_subtopics = []
    page_content = []

    for entry in dynamic_zone_entries:
        if entry["component"] == "ikan.subchapter-subtopics":
            subchapter_subtopics = entry["data"]
        else:
            page_content.append(entry["data"])

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "id": item.get("id"),
            "type": "learning_hub_subchapter",
            "language": item.get("locale"),
            "pageIcon": aggregate_image(item.get("page_icon"), base_url),
            "pageAudio": aggregate_media_reference(item.get("page_audio"), base_url) or empty_media(),
            "pageTitle": item.get("page_title") or "Title",
            "pageVideo": aggregate_media_reference(item.get("page_video"), base_url) or empty_media(),
            "page_name": item.get("uid"),
            "subchapter": item.get("subchapter"),
            "pageContent": page_content,
            "disclaimerText": item.get("disclaimer_text"),
            "pageTitleAudio": aggregate_media_reference(item.get("title_audio"), base_url) or empty_media(),
            "pageDescription": aggregate_rich_text(item.get("page_description")),
            "subchapterSummary": aggregate_rich_text(item.get("subchapter_summary")),
            "analyticsEventName": item.get("analytics_event_name"),
            "subchapterSubtopics": subchapter_subtopics,
        },
    )


def aggregate_sub_chapter_list(item, **context):
    base_url = context.get("base_url")
    page_content = aggregate_dynamic_zone(
        item.get("dynamic_zone", []),
        base_url=base_url,
    )

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "id": item.get("prismic_id") or item.get("id"),
            "type": "sub_chapter_list",
            "language": item.get("locale"),
            "pageIcon": aggregate_image(item.get("page_icon"), base_url),
            "pageAudio": aggregate_media_reference(item.get("page_audio"), base_url) or empty_media(),
            "pageTitle": item.get("page_title") or "Title",
            "pageVideo": aggregate_media_reference(item.get("page_video"), base_url) or empty_media(),
            "page_name": item.get("uid"),
            "pageContent": page_content,
            "disclaimerText": item.get("disclaimer_text"),
            "pageTitleAudio": aggregate_media_reference(item.get("title_audio"), base_url),
            "pageDescription": aggregate_rich_text(item.get("page_description")),
            "analyticsEventName": item.get("analytics_event_name"),
        },
    )


def aggregate_learning_hub_subchapter_list(item, **context):
    base_url = context.get("base_url")
    page_content = aggregate_dynamic_zone(
        item.get("dynamic_zone", []),
        base_url=base_url,
    )

    return (
        item.get("uid"),
        item.get("locale"),
        {
            "id": item.get("prismic_id") or item.get("id"),
            "type": "learning_hub_subchapter_list",
            "chapter": item.get("chapter"),
            "language": item.get("locale"),
            "pageIcon": aggregate_image(item.get("page_icon"), base_url),
            "pageAudio": aggregate_media_reference(item.get("page_audio"), base_url),
            "pageTitle": item.get("page_title") or "Title",
            "pageVideo": aggregate_media_reference(item.get("page_video"), base_url),
            "page_name": item.get("uid"),
            "pageContent": page_content,
            "disclaimerText": item.get("disclaimer_text"),
            "pageTitleAudio": aggregate_media_reference(item.get("title_audio"), base_url),
            "pageDescription": aggregate_rich_text(item.get("page_description")),
            "analyticsEventName": item.get("analytics_event_name"),
        },
    )


CUSTOM_TYPE_AGGREGATORS = {
    "app_tutorials": aggregate_app_tutorials,
    "case_study": aggregate_case_study,
    "common_text": aggregate_common_text,
    "create_content_area": aggregate_create_content_area,
    "form_questions": aggregate_form_questions,
    "language_text": aggregate_language_text,
    "menu_content": aggregate_menu_content,
    "page": aggregate_page,
    "sub_chapter_list": aggregate_sub_chapter_list,
    "learning_hub_subchapter": aggregate_learning_hub_subchapter,
    "learning_hub_subchapter_list": aggregate_learning_hub_subchapter_list,
}
