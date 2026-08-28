import re


def normalize_link_url(url):
    if not isinstance(url, str):
        return url

    normalized_url = url.strip()

    mailto_match = re.match(r"^(mailto:)+", normalized_url, flags=re.IGNORECASE)
    if mailto_match:
        remainder = normalized_url[mailto_match.end():]
        if remainder.lower().startswith(("http://", "https://")):
            normalized_url = remainder
        else:
            normalized_url = f"mailto:{remainder}"

    tel_match = re.match(r"^(tel:)+", normalized_url, flags=re.IGNORECASE)
    if tel_match:
        remainder = normalized_url[tel_match.end():]
        if remainder.lower().startswith(("http://", "https://")):
            normalized_url = remainder
        else:
            normalized_url = f"tel:{remainder}"

    return normalized_url


def aggregate_tutorials_component(tutorials_component, base_url, **_context):
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


def aggregate_additional_text_component(additional_text_component, **_context):
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


def aggregate_common_text_component(component, **_context):
    return {
        "label": component.get("key"),
        "value": component.get("value"),
    }


def aggregate_menu_content_component(component, **_context):
    icon = component.get("icon")
    roles = component.get("roles")
    icon_path = component.get("icon_path")
    return {
        "key": component.get("key"),
        "url": component.get("url"),
        "icon": icon or None,
        "label": component.get("label"),
        "roles": roles or None,
        "title": component.get("title"),
        "enabled": component.get("enabled"),
        "position": component.get("position"),
        "icon_path": icon_path or None,
    }


def aggregate_page_media_component(component, base_url, **_context):
    media_key = component.get("media_key")
    media_value = component.get("media_value")
    if not media_key or not media_value:
        return None

    return {
        "media_key": media_key,
        "media_value": aggregate_media_reference(media_value, base_url),
    }


def aggregate_language_text_component(component, **_context):
    return {
        "key": component.get("key"),
        "label": component.get("label"),
        "locale_code": component.get("locale_code"),
    }


def aggregate_subchapter_subtopics_component(component, **_context):
    return [
        {
            "id": item.get("subtopic_id"),
            "title": item.get("subtopic_title"),
        }
        for item in component.get("repeatable_zone", [])
        if item.get("subtopic_id") or item.get("subtopic_title")
    ]


def aggregate_audio_component(component, base_url, **_context):
    return {
        "type": "audio",
        "title": component.get("audio_title"),
        "description": aggregate_rich_text(component.get("audio_description")),
        "mediaData": aggregate_media_reference(component.get("audio_link"), base_url),
    }


def parse_inline_str_comma_separated_options(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        return value.split(",") if value and value.strip() else []
    return []


def aggregate_form_question_options(options, options_translations=None):
    option_values = parse_inline_str_comma_separated_options(options)
    if not option_values:
        return []

    translated_values = parse_inline_str_comma_separated_options(options_translations)
    if translated_values:
        return [
            {
                "label": label,
                "value": value,
            }
            for label, value in zip(translated_values, option_values)
        ]

    return [
        {
            "label": value,
            "value": value,
        }
        for value in option_values
    ]


def aggregate_form_question_component(component, **_context):
    return {
        "category": component.get("category"),
        "key": component.get("key"),
        "label": component.get("label"),
        "placeholder": component.get("placeholder"),
        "question_type": component.get("question_type"),
        "is_required": component.get("is_required"),
        "displayquestion": component.get("displayquestion"),
        "help_text": component.get("helptext"),
        "options": aggregate_form_question_options(
            component.get("options"),
            component.get("options_translations"),
        ),
    }


def aggregate_rich_text(blocks):
    if not blocks:
        return None

    result = []
    for block in blocks:
        block_type = block.get("type")
        if block_type == "paragraph":
            result.append({"paragraph": render_children_text(block.get("children", []))})
        elif block_type == "heading":
            level = block.get("level", 1)
            result.append({f"heading{level}": render_children_text(block.get("children", []))})
        elif block_type == "list":
            list_items = []
            for child in block.get("children", []):
                if child.get("type") != "list-item":
                    continue
                list_items.append(render_children_text(child.get("children", [])))
            result.append(
                {
                    "orderedList" if block.get("format") == "ordered" else "unorderedList": list_items,
                }
            )
    return result or None


def render_rich_text_as_plain_text(blocks):
    if not blocks:
        return None

    parts = []
    for block in blocks:
        text = render_children_text(block.get("children", []))
        if text:
            parts.append(text)
    if not parts:
        return ""
    return " ".join(parts).strip()


def aggregate_option_entries(value):
    if not value:
        return []

    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]

    if isinstance(value, list):
        return [
            render_children_text(item.get("children", [])).strip()
            for item in value
            if render_children_text(item.get("children", [])).strip()
        ]

    return []


def aggregate_web_link(url):
    if not url:
        return None

    return {
        "url": url,
        "kind": "web",
        }


def aggregate_media_reference(value, base_url):
    if not value:
        return None

    if isinstance(value, str):
        return aggregate_web_link(value)

    mime = value.get("mime", "")
    if mime.startswith("image/"):
        return aggregate_image(value, base_url)

    return aggregate_media(value, base_url)


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


def aggregate_text_area_component(zone, base_url=None, include_audio=True, **_context):
    aggregated_text_area = aggregate_text_area(zone)
    if not include_audio:
        return aggregated_text_area

    aggregated_text_area["contentAudio"] = (
        aggregate_media_reference(zone.get("content_audio"), base_url) or empty_media()
    )
    return aggregated_text_area


def aggregate_question_component(zone, base_url, **_context):
    return {
        "key": zone.get("question_key"),
        "type": "questions",
        "roles": split_roles(zone.get("roles")) if zone.get("roles") else None,
        "options": aggregate_question_options(zone.get("repeatable_zone", [])),
        "question": render_rich_text_as_plain_text(zone.get("question")),
        "isRequired": zone.get("is_required"),
        "questionType": zone.get("question_type"),
        "questionAudio": aggregate_media_reference(zone.get("question_audio"), base_url) or empty_media(),
        "displayquestion": bool(zone.get("display_question")),
    }


def aggregate_warning_box_component(zone, base_url, **_context):
    return {
        "icon": aggregate_image(zone.get("icon"), base_url),
        "type": "warning_box",
        "title": zone.get("warning_title"),
        "description": aggregate_rich_text(zone.get("warning_text")),
    }


def aggregate_dropdown_content_component(zone, base_url, **_context):
    return {
        "type": "drop_down_content",
        "data": [
            {
                "title": entry.get("title"),
                "titleAudio": aggregate_media_reference(entry.get("audio"), base_url) or {},
                "description": aggregate_rich_text(entry.get("description")),
                "showDescription": False,
            }
            for entry in zone.get("repeatable_zone", [])
        ],
    }


def aggregate_clickable_list_component(zone, **_context):
    base_url = _context.get("base_url")
    items = []

    for item in zone.get("repeatable_zone", []):
        icon = aggregate_image(item.get("icon"), base_url)
        page_reference = item.get("page")
        page = None

        if page_reference:
            page = {"uid": page_reference}

        items.append(
            {
                "icon": icon.get("url") if icon else None,
                "label": render_rich_text_as_plain_text(item.get("label")),
                "navigationPage": None,
                "page": page,
            }
        )

    return {
        "type": "clickable_list",
        "layout": (zone.get("layout") or "flow").lower(),
        "list": items,
    }


def aggregate_case_study_component(
    zone,
    **_context,
):
    existing_content = _context.get("existing_content")
    parent_uid = _context.get("parent_uid")
    locale = _context.get("locale")
    link = zone.get("link") or {}
    linked_uid = link.get("uid") if isinstance(link, dict) else link
    linked_locale = link.get("locale") if isinstance(link, dict) else None
    existing_case_study = find_existing_aggregated_case_study(
        existing_content,
        linked_uid,
        linked_locale or locale,
    )
    if existing_case_study is None:
        return None

    return {
        **existing_case_study,
        "subChapter": parent_uid,
    }


def aggregate_video_area_component(zone, base_url, **_context):
    return {
        "type": "video",
        "mediaData": aggregate_media_reference(zone.get("video_link"), base_url),
        "thumbnail": aggregate_image(zone.get("thumbnail"), base_url),
    }


def aggregate_single_image_component(zone, base_url, **_context):
    return {
        "type": "image",
        "title": zone.get("key"),
        "mediaData": aggregate_image(zone.get("single_image"), base_url),
    }


def aggregate_heading_component(zone, base_url, **_context):
    return {
        "text": zone.get("heading"),
        "type": "heading",
        "headingAudio": aggregate_media_reference(zone.get("heading_audio"), base_url) or empty_media(),
    }


def empty_media():
    return {
        "url": None,
        "kind": "media",
    }


def split_roles(value):
    if not value:
        return []
    return [role.strip() for role in re.split(r",\s*|\s*,\s*", value) if role.strip()]


def render_children_text(children):
    parts = []
    for child in children or []:
        child_type = child.get("type")
        if child_type == "text":
            parts.append(render_text_node(child))
        elif child_type == "link":
            href = normalize_link_url(child.get("url"))
            text = render_children_text(child.get("children", []))
            parts.append(f'<a href="{href}">{text}</a>' if href else text)
        elif child_type == "list-item":
            parts.append(render_children_text(child.get("children", [])))
        else:
            nested_children = child.get("children")
            if nested_children is not None:
                parts.append(render_children_text(nested_children))
    return "".join(parts)


def render_text_node(node):
    text = node.get("text", "")
    if node.get("bold"):
        text = f"<strong>{text}</strong>"
    if node.get("italic"):
        text = f"<em>{text}</em>"
    if node.get("underline"):
        text = f"<u>{text}</u>"
    return text


def aggregate_question_options(repeatable_zone):
    options = []

    for item in repeatable_zone:
        option_values = aggregate_option_entries(item.get("options"))
        if not option_values:
            continue

        if len(option_values) > 1:
            for option in option_values:
                options.append(
                    {
                        "option": option,
                        "description": None,
                        "followUpQuestion": None,
                    }
                )
            continue

        follow_up_options = aggregate_option_entries(item.get("follow_up_question_options"))
        options.append(
            {
                "option": option_values[0] if option_values else None,
                "description": render_rich_text_as_plain_text(item.get("option_description"))
                if isinstance(item.get("option_description"), list)
                else item.get("option_description"),
                "followUpQuestion": (
                    {
                        "key": item.get("follow_up_question_key"),
                        "roles": split_roles(item.get("roles")) if item.get("roles") else None,
                        "options": [
                            {
                                "option": option,
                                "description": None,
                                "secondFollowUpQuestion": None,
                            }
                            for option in follow_up_options
                        ]
                        or None,
                        "question": item.get("follow_up_question"),
                        "isRequired": item.get("is_required"),
                        "questionLink": item.get("follow_up_question_link") or None,
                        "questionType": item.get("follow_up_question_type"),
                        "displayquestion": bool(item.get("display_followup_question")),
                    }
                    if item.get("follow_up_question")
                    else None
                ),
            }
        )

    return options


def find_existing_aggregated_case_study(existing_content, uid, locale):
    if not isinstance(existing_content, dict) or not uid or not locale:
        return None

    locale_pages = existing_content.get(locale)
    if not isinstance(locale_pages, dict):
        return None

    existing_page = locale_pages.get(uid)
    if not isinstance(existing_page, dict):
        return None

    if existing_page.get("type") != "case_study":
        return None

    return existing_page


DYNAMIC_ZONE_COMPONENT_AGGREGATORS = {
    "ikan.additional-text": aggregate_additional_text_component,
    "ikan.clickable-list": aggregate_clickable_list_component,
    "ikan.common-text": aggregate_common_text_component,
    "ikan.dropdown-content": aggregate_dropdown_content_component,
    "ikan.heading": aggregate_heading_component,
    "ikan.language-text": aggregate_language_text_component,
    "ikan.menu-content": aggregate_menu_content_component,
    "ikan.media": aggregate_page_media_component,
    "ikan.audio": aggregate_audio_component,
    "ikan.case-study-linked": aggregate_case_study_component,
    "ikan.question": aggregate_question_component,
    "ikan.subchapter-subtopics": aggregate_subchapter_subtopics_component,
    "ikan.single-image": aggregate_single_image_component,
    "ikan.text-area": aggregate_text_area_component,
    "ikan.tutorials": aggregate_tutorials_component,
    "ikan.warning-box": aggregate_warning_box_component,
    "ikan.video-area": aggregate_video_area_component,
    "jgw.case-study": aggregate_case_study_component,
    "jgw.warning-box": aggregate_warning_box_component,
}
