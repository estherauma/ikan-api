import re


def aggregate_tutorials(dynamic_zone, base_url):
    tutorials_component = next(
        (item for item in dynamic_zone if item.get("__component") == "ikan.tutorials"),
        None,
    )
    if not tutorials_component:
        return None

    items = []
    for item in tutorials_component.get("repeatable_zone", []):
        items.append(
            {
                "roles": split_roles(item.get("roles")),
                "item_icon": item.get("item_icon"),
                "item_text": aggregate_text(item.get("item_text")),
                "item_audio": empty_media(),
                "item_title": item.get("item_title"),
                "item_video": aggregate_media(item.get("item_video"), base_url),
                "item_analytics_event_name": item.get("item_analytics_event_name"),
            }
        )

    return {
        "items": items,
        "intro_text": aggregate_text(tutorials_component.get("intro_text"), split_lines=True),
        "intro_audio": empty_media(),
        "intro_title": tutorials_component.get("intro_title"),
        "analytics_event_name": tutorials_component.get("analytic_event_name"),
    }


def aggregate_additional_text(dynamic_zone):
    additional_text_component = next(
        (item for item in dynamic_zone if item.get("__component") == "ikan.additional-text"),
        None,
    )
    if not additional_text_component:
        return None

    result = []
    for item in additional_text_component.get("repeatable_zone", []):
        if item.get("value") is None:
            continue
        result.append(
            {
                "type": "paragraph",
                "label": item.get("key"),
                "value": item.get("value"),
            }
        )
    return result


def aggregate_text(value, split_lines=False):
    if not value:
        return None

    if split_lines:
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        return [{"paragraph": line} for line in lines] or None

    return [{"paragraph": value}]


def aggregate_media(media, base_url):
    if not media:
        return None

    url = media.get("url")
    if url and url.startswith("/"):
        url = f"{base_url.rstrip('/')}{url}"

    return {
        "url": url,
        "kind": "media",
        "name": media.get("name", "unknown"),
        "size": str(media.get("size")) if media.get("size") is not None else "unknown",
    }


def aggregate_image(media, base_url):
    if not media:
        return None

    url = media.get("url")
    if url and url.startswith("/"):
        url = f"{base_url.rstrip('/')}{url}"

    dimensions = None
    if media.get("width") is not None or media.get("height") is not None:
        dimensions = {
            "width": media.get("width"),
            "height": media.get("height"),
        }

    return {
        "url": url,
        "kind": "image",
        "name": media.get("alternativeText"),
        "dimensions": dimensions,
    }


def aggregate_text_area(zone):
    return {
        "type": "text_area",
        "title": zone.get("title"),
        "identifier": zone.get("identifier"),
        "description": aggregate_rich_text(zone.get("text_area")),
        "contentAudio": None,
    }


def aggregate_rich_text(blocks):
    if not blocks:
        return None

    result = []
    for block in blocks:
        if block.get("type") != "paragraph":
            continue
        children = block.get("children") or []
        text = "".join(child.get("text", "") for child in children).strip()
        if text:
            result.append({"paragraph": text})
    return result or None


def empty_media():
    return {
        "url": None,
        "kind": "media",
        "name": "unknown",
        "size": "unknown",
    }


def split_roles(value):
    if not value:
        return []
    return [role.strip() for role in re.split(r",\s*|\s*,\s*", value) if role.strip()]
