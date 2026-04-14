import requests
from decouple import config
from prismic.models import AggregatedContent, MessagingContent, PushNotificationsContent
import re


class PrismicAPI():
    def __init__(self) -> None:
        self.api_url = config('PRISMIC_API_URL')
        self.access_token = config('PRISMIC_ACCESS_TOKEN')
        self.master_ref_data = self.get_master_ref_response()
        self.master_ref = self.get_master_ref(self.master_ref_data)
        self.languages = self.get_languages(self.master_ref_data)
        self.initiate_document_fetch()

    def build_url(self, url='', type='master_ref'):
        if type == 'master_ref':
            return f'{self.api_url}?access_token={self.access_token}'

        if type == 'doc_search':
            return f'{self.api_url}/documents/search?ref={self.master_ref}&'\
                f'access_token={self.access_token}&pageSize=100'

    def get_master_ref_response(self):
        url = self.build_url()
        req = requests.get(url)
        req.raise_for_status()
        data = req.json()
        return data

    def get_master_ref(self, data):
        if data['refs']:
            return data['refs'][0]['ref']
        else:
            'Master ref not available'

    def get_languages(self, data):
        return data['languages']

    def initiate_document_fetch(self):
        documents = {}
        url = self.build_url(type='doc_search')
        for language in self.languages:
            lang_id = language['id']
            lang_url = f'{url}&lang={lang_id}'
            documents[lang_id] = self.get_documents(url=lang_url)
        #  ToDo: Find a better place to place this logic for storing the content
        aggregated_content = AggregatedContent()
        aggregated_content.content = documents
        aggregated_content.save()

    def get_documents(self, url):
        req = requests.get(url)
        req.raise_for_status()
        docs_data = req.json()
        agg_data = self.aggr_data(docs_data)
        return agg_data

    def aggr_data(self, data):
        aggregated_data = {}

        def agg_form_questions(form_data):
            question_data = []
            additional_text = []
            for question in form_data:

                if question['slice_type'] == 'form_question':
                    category, key, label, placeholder, question_type, is_required, displayquestion, \
                        help_text, options, options_translations = question['primary'].values()
                    final_options_array = []
                    if options is not None:
                        # split string by comma and remove any leading or trailing spaces
                        options = re.split(r',\s*|\s*,\s*', options)
                        option_list = []
                        for option in options:
                            # TODO: Leaving this for things entries we already have on prismic as a fall back.
                            # Once all are updated, we can remove this
                            new_options_dict = {"value": option, "label": option}
                            option_list.append(new_options_dict)
                            final_options_array = option_list

                    if options_translations and options:
                        # split string by comma and remove any leading or trailing spaces
                        options_translations = re.split(r',\s*|\s*,\s*', options_translations)
                        final_options_array = [{"value": value, "label": key} for key, value
                                               in zip(options_translations, options)]
                    question_data.append(
                        {
                            'category': category,
                            'key': key,
                            'label': label,
                            'placeholder': placeholder,
                            'question_type': question_type,
                            'displayquestion': displayquestion,
                            'help_text': help_text,
                            'options': final_options_array,
                            'is_required': is_required
                        })
                elif question['slice_type'] == 'additional_text':
                    for entry in question['items']:
                        slice_data = aggregate_text_data(entry['value']) if entry['value'] else []
                        for x in slice_data:
                            for content_type, value in x.items():
                                additional_text.append({
                                    'label': entry['key'],
                                    'value': value,
                                    'type': content_type
                                })
            return question_data, additional_text

        def agg_page_text(page_data):
            additional_text = []
            for data in page_data:
                if data['slice_type'] == 'additional_text':
                    for entry in data['items']:
                        slice_data = aggregate_text_data(entry['value']) if entry['value'] else []
                        for x in slice_data:
                            for content_type, value in x.items():
                                additional_text.append({
                                    'label': entry['key'],
                                    'value': value,
                                    'type': content_type
                                })
            return additional_text

        def agg_common_text(common_text_data):
            '''Aggregrate common text'''
            aggr_common_content = []
            for x in common_text_data:
                aggr_common_content.append(x['primary'])
            return aggr_common_content

        def agg_side_menu(menu_data):
            return [menu['primary'] for menu in menu_data]

        def agg_intro_content(intro_data):
            return [data['primary'] for data in intro_data]

        def agg_welcome_screens_slides(slides):
            result = []
            for slide in slides:
                slide_obj = {
                    **slide,
                    'slide_audio': aggregate_media_data(slide.get('slide_audio')) if slide.get('slide_audio') else None,
                    'slide_content': aggregate_text_data(slide.get('slide_content'))
                    if slide.get('slide_content') else None,
                }
                result.append(slide_obj)
            return result

        def agg_tutorials_slice(data):
            if not data:
                return None
            result = {
                'intro_title': data['primary'].get('intro_title'),
                'intro_text': aggregate_text_data(data['primary'].get('intro_text'))
                if data['primary'].get('intro_text') else None,
                'intro_audio': aggregate_media_data(data['primary'].get('intro_audio'))
                if data['primary'].get('intro_audio') else None,
                'analytics_event_name': data['primary'].get('analytics_event_name'),
                'items': []
            }
            for item in data['items']:
                # split string by comma and remove any leading or trailing spaces
                roles = item.get('roles') if item.get('roles') else None
                roles_list = re.split(r',\s*|\s*,\s*', roles) if roles else []
                item_obj = {
                    'item_icon': item.get('item_icon'),
                    'item_title': item.get('item_title'),
                    'item_text': aggregate_text_data(item.get('item_text')) if item.get('item_text') else None,
                    'item_audio': aggregate_media_data(item.get('item_audio')) if item.get('item_audio') else None,
                    'item_video': aggregate_media_data(item.get('item_video')) if item.get('item_video') else None,
                    'item_analytics_event_name': item.get('item_analytics_event_name'),
                    'roles': roles_list,
                }
                result['items'].append(item_obj)
            return result

        for item in data['results']:
            if item['type'] == 'form_questions':
                aggregation_response = agg_form_questions(item['data']['body'])
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'form_questions': aggregation_response[0],
                    'additional_text': aggregation_response[1],
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'common_text' or item['type'] == 'language_text':
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'data': agg_common_text(item['data']['body'])
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'menu_content':
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'data': agg_side_menu(item['data']['body'])
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'intro_content':
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'data': agg_intro_content(item['data']['body'])
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'create_content_area' or\
                    item['type'] == 'sub_chapter_list' or\
                    item['type'] == 'learning_hub_subchapter_list':
                content = aggregate_content(data['results'])
                aggregated_data = {**aggregated_data, **content}

            if item['type'] == 'page':
                item_body = item['data']['body'] if 'body' in item['data'] and item['data']['body'] else None
                page_media = {}
                additional_text = None
                if item_body:
                    for i in item_body:
                        if i['slice_type'] == 'media':
                            if i['primary']['media_key'] and i['primary']['media_value']:
                                media_key = i['primary']['media_key']
                                media_value = aggregate_media_data(i['primary']['media_value'])
                                page_media[media_key] = media_value
                        if i['slice_type'] == 'additional_text':
                            additional_text = agg_page_text([i])
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'additional_text': additional_text,
                    'page_media': page_media,
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'welcome_screens':
                slides = agg_welcome_screens_slides(item['data']['slides'])
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'show_slides': item['data']['show_slides'],
                    'slides': slides,
                    'analyticsEventName': item['data']['analytics_event_name'],
                    'last_updated': item['last_publication_date'],
                }
                aggregated_data[item['uid']] = page_data

            if item['type'] == 'app_tutorials':
                item_body = item['data']['body'] if 'body' in item['data'] and item['data']['body'] else None
                tutorials = None
                additional_text = None
                if item_body:
                    for i in item_body:
                        if i['slice_type'] == 'tutorials':
                            tutorials = agg_tutorials_slice(i)
                        if i['slice_type'] == 'additional_text':
                            additional_text = agg_page_text([i])
                page_data = {
                    'page_name': item['uid'],
                    'welcome_title': item['data']['welcome_title'],
                    'welcome_text': aggregate_text_data(item['data']['welcome_text'])
                    if item['data']['welcome_text'] else None,
                    'welcome_audio': aggregate_media_data(item['data']['welcome_audio'])
                    if item['data']['welcome_audio'] else None,
                    'welcome_video': aggregate_media_data(item['data']['welcome_video'])
                    if item['data']['welcome_video'] else None,
                    'additional_text': additional_text,
                    'tutorials': tutorials,
                    'analyticsEventName': item['data']['analytics_event_name'],
                    'last_updated': item['last_publication_date'],
                }
                aggregated_data[item['uid']] = page_data

        return aggregated_data


class PrismicMessagingAPI():
    def __init__(self, req, access_token):
        self.messaging_api_url = config('PRISMIC_MESSAGING_API_URL')
        self.messaging_access_token = config('PRISMIC_MESSAGING_ACCESS_TOKEN')
        self.data = req.data
        self.doc_ref = self.data['documents'][0] if self.data['documents'] else None
        self.access_token = access_token

    # one doc is published at a time
    def get_published_content(self):
        masterRef = self.data.get('master_ref', None)
        url = f'{self.messaging_api_url}/documents/search?ref={masterRef}&lang=*'\
            f'&q=[[at(document.id, "{self.doc_ref}")]]&access_token={self.access_token}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        res_data = data['results']

        return {
            'content': res_data,
            'aggregated_content': self.format_aggregated_content(res_data),
        }

    def get_all_documents(self):
        masterRef = self.data.get('master_ref', None)
        url = f'{self.messaging_api_url}/documents/search?ref={masterRef}&lang=*&access_token={self.access_token}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        res_data = data['results']

        return {
            'content': res_data,
            'aggregated_content': self.format_aggregated_content(res_data),
        }

    def format_aggregated_content(self, content_to_agg):
        db_messaging_content = MessagingContent.objects.first()
        saved_agg_content = getattr(db_messaging_content, 'aggregated_content') if db_messaging_content else None

        if content_to_agg and saved_agg_content is None:
            result = {}
            agg_content = aggregate_content(content_to_agg)
            for key, value in agg_content.items():
                lang = value['language']
                if lang not in result:
                    result[lang] = agg_content
                else:
                    result[lang] = {**result[lang], **agg_content}
            return result

        elif content_to_agg and saved_agg_content:
            agg_content = aggregate_content(content_to_agg)
            if bool(agg_content):
                final_data = {}
                for el, value in agg_content.items():
                    lang = value['language']
                    updated_data = agg_content[el]
                    saved_data = saved_agg_content.get(lang, None)
                    saved_data[el] = updated_data

                    if lang not in final_data:
                        final_data[lang] = saved_data
                    else:
                        final_data[lang] = {**final_data[lang], **saved_data}
                return final_data
            else:
                return None


class PrismicPushNotificationAPI():
    def __init__(self, req, access_token):
        self.push_notification_api_url = config('PUSH_NOTIFICATION_CMS_API_URL')
        self.push_notification_access_token = config('PUSH_NOTIFICATION_CMS_ACCESS_TOKEN')
        self.data = req.data
        self.doc_ref = self.data['documents'][0] if self.data['documents'] else None
        self.access_token = access_token

    def get_published_notif_content(self):
        masterRef = self.data.get('master_ref', None)
        url = f'{self.push_notification_api_url}/documents/search?ref={masterRef}&lang=*'\
            f'&q=[[at(document.id, "{self.doc_ref}")]]&access_token={self.access_token}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        res_data = data['results']

        return {
            'content': res_data,
            'aggregated_content': self.aggregate_push_notification(res_data),
        }

    def aggregate_push_notification(self, notif_to_agg):
        db_messaging_content = PushNotificationsContent.objects.first()
        saved_agg_content = getattr(db_messaging_content, 'aggregated_content') if db_messaging_content else None

        if notif_to_agg and saved_agg_content is None:
            result = {}
            agg_notif_content = aggregate_content(notif_to_agg)
            for key, value in agg_notif_content.items():
                lang = value['language']
                if lang not in result:
                    result[lang] = agg_notif_content
                else:
                    result[lang] = {**result[lang], **agg_notif_content}
            return result
        elif notif_to_agg and saved_agg_content:
            agg_notif_content = aggregate_content(notif_to_agg)
            if bool(agg_notif_content):
                final_data = {}
                for el, value in agg_notif_content.items():
                    lang = value['language']
                    updated_data = agg_notif_content[el]
                    saved_data = saved_agg_content.get(lang, None)
                    saved_data[el] = updated_data

                    if lang not in final_data:
                        final_data[lang] = saved_data
                    else:
                        final_data[lang] = {**final_data[lang], **saved_data}
                return final_data
            else:
                return None


def aggregate_content(data):
    agg_data = {}

    for item in data:
        if item['type'] == 'message' or\
                item['type'] == 'create_content_area' or\
                item['type'] == 'sub_chapter_list' or\
                item['type'] == 'learning_hub_subchapter_list' or\
                item['type'] == 'learning_hub_subchapter':
            page_data = {
                'id': item['id'],
                'page_name': item['uid'],
                'type': item['type'],
                'language': item['lang'],
                'pageTitle': item['data'].get('page_title')[0].get('text') if item['data'].get('page_title')
                else 'Title',
                'disclaimerText': item['data'].get('disclaimer_text') if item['data'].get('disclaimer_text') else None,
                'pageTitleAudio': aggregate_media_data(item['data'].get('title_audio'))
                if item['data'].get('title_audio') else None,
                'pageDescription': aggregate_text_data(item['data'].get('page_description')) if item['data'].get(
                    'page_description') else None,
                'pageAudio': aggregate_media_data(item['data'].get('page_audio')) if item['data'].get(
                    'page_audio') else None,
                'pageVideo': aggregate_media_data(item['data'].get('page_video')) if item['data'].get(
                    'page_video') else None,
                'pageIcon': aggregate_media_data(item['data'].get('page_icon'))
                if item['data'].get('page_icon') else None,
                'pageContent': [],
                'analyticsEventName': item['data'].get('analytics_event_name')
                if item['data'].get('analytics_event_name') else None,
            }

            # Add userRole to message page_data
            if item['type'] == 'message':
                page_data['userRole'] = item['data'].get('user_role') if item['data'].get('user_role') else None

            # Add chapter number to learning hub subchapter list page_data
            if item['type'] == 'learning_hub_subchapter_list':
                page_data['chapter'] = item['data'].get('chapter') if item['data'].get('chapter') else None

            # Add summary and subtopics to learning hub subchapter page_data
            if item['type'] == 'learning_hub_subchapter':
                page_data['subchapter'] = item['data'].get('subchapter') if item['data'].get('subchapter') else None
                page_data['subchapterSummary'] = aggregate_text_data(item['data'].get('subchapter_summary')) if \
                    item['data'].get('subchapter_summary') else None
                subtopics = []
                if item['data'].get('subchapter_subtopics'):
                    for subtopic in item['data']['subchapter_subtopics']:
                        subtopics.append({
                            'id': subtopic.get('subtopic_id'),
                            'title': subtopic.get('subtopic_title'),
                        })
                page_data['subchapterSubtopics'] = subtopics

            if 'body' in item['data'] and item['data']['body']:
                page_content = item['data']['body']
                for el in page_content:
                    slice_data = format_common_slice_data(item=el, pagesList=data, page=item, page_content=page_content)
                    # Add subtopic id to slice data if slice is a learning hub subchapter and subtopic id exists
                    if (
                            item['type'] == 'learning_hub_subchapter'
                            and el['primary'].get('subtopic_id')
                            and isinstance(slice_data, dict)
                    ):
                        slice_data['subtopicId'] = el['primary'].get('subtopic_id')

                    page_data['pageContent'].append(slice_data)
            if item['uid'] is not None:
                agg_data[item['uid']] = page_data
            else:
                agg_data[item['id']] = page_data

        if item['type'] == 'case_study':
            case_study = format_case_study(item)
            agg_data[item['uid']] = case_study

        if item['type'] == 'notification':
            vessels = item['data'].get('vessels') if item['data'].get('vessels') else None

            # split string by comma and remove any leading or trailing spaces
            vessels_list = re.split(r',\s*|\s*,\s*', vessels) if vessels else []
            notif_result = {
                'id': item['id'],
                'uid': item['uid'],
                'type': item['type'],
                'language': item['lang'],
                'notifData': {
                   'enTitle': item['data'].get('en-title') if item['data'].get('en-title') else None,
                   'zhTitle': item['data'].get('zh-title') if item['data'].get('zh-title') else None,
                   'idTitle': item['data'].get('id-title') if item['data'].get('id-title') else None,
                   'enBody': item['data'].get('en-body') if item['data'].get('en-body') else None,
                   'zhBody': item['data'].get('zh-body') if item['data'].get('zh-body') else None,
                   'idBody': item['data'].get('id-body') if item['data'].get('id-body') else None,
                   'userRole': item['data'].get('user-role') if item['data'].get('user-role') else None,
                   'vessels': vessels_list,
                }
            }
            agg_data[item['uid']] = notif_result
    return agg_data


def aggregate_media_data(data):
    if not data:
        return None
    aggregated_media_data = {}
    media_type = data.get('type') if data.get('type') else None
    link_type = data.get('link_type') if data.get('link_type') else None
    if link_type:
        if link_type == 'Media':
            aggregated_media_data = {
                'name': data.get('name', 'unknown'),
                'kind': 'media',
                'url': data.get('url', None),
                'size': data.get('size', 'unknown')
            }
        elif link_type == 'Web':
            aggregated_media_data = {
                'name': 'unknown',
                'kind': 'web',
                'url': data.get('url', None),
                'size': 'unknown'
            }
    elif media_type:
        if media_type == 'Link.file':
            aggregated_media_data = data.get('file')
        elif media_type == 'Link.web':
            aggregated_media_data = {
                'name': 'unknown',
                'kind': 'web',
                'url': data.get('url', None),
                'size': 'unknown'
            }
        elif media_type == 'Image':
            aggregated_media_data = {
                'name': data.get('alt', 'unknown'),
                'kind': 'image',
                'url': data.get('url', None),
                'dimensions': data.get('dimensions', None),
            }
    elif data is not None:
        aggregated_media_data = {
            'name': data.get('alt', 'unknown'),
            'kind': 'image',
            'url': data.get('url', None),
            'dimensions': data.get('dimensions', None),
        }
    else:
        aggregated_media_data = None
    return aggregated_media_data


def aggregate_text_data(data):
    list_of_details = []
    index = 0
    while index < len(data):
        item = data[index]
        if 'heading' in item['type']:
            list_of_details.append({
                item['type']: item['text']
            })
        else:
            if item['type'] == 'paragraph':
                list_of_details.append({
                    'paragraph': add_spans(item)
                })
            elif item['type'] == 'image':
                list_of_details.append({
                    'image': item.get('url')
                })
            elif item['type'] == 'list-item':
                unordered_list = []
                i = index
                while i < len(data) and data[i]['type'] == 'list-item':
                    unordered_list.append(add_spans(data[i]))
                    i += 1
                index = i - 1
                list_of_details.append({
                    'unorderedList': unordered_list
                })
            elif item['type'] == 'o-list-item':
                ordered_list = []
                i = index
                while i < len(data) and data[i]['type'] == 'o-list-item':
                    ordered_list.append(add_spans(data[i]))
                    i += 1
                index = i - 1
                list_of_details.append({
                    'orderedList': ordered_list
                })
        index += 1
    return list_of_details


def add_spans(text_data):
    def text_format_is_subset(current, prev):
        """
            Checks if there is a text format that is a subset of another text format
            Returns True if there is a subset, False otherwise
        """
        current_start, current_end = current['start'], current['end']
        previous_start, previous_end = prev['start'], prev['end']

        if current_start >= previous_start and current_end <= previous_end:
            return True
        return False

    if not text_data:
        return None

    orginal_text = text_data.get('text', '')
    formated_text = text_data.get('text', '')
    if (text_data['type'] in ['paragraph', 'list-item', 'o-list-item']) and text_data.get('spans'):
        if len(text_data['spans']) == 1:
            for span in text_data['spans']:
                if span['type'] == 'hyperlink':
                    paragraph = formated_text
                    link_text = paragraph[span['start']:span['end']]
                    html_link = f'<a href="{span["data"]["url"]}">{link_text}</a>'
                    formated_text = paragraph[:span['start']] + html_link + paragraph[span['end']:]
                elif span['type'] == 'strong':
                    paragraph = formated_text
                    text_to_bold = paragraph[span['start']:span['end']]
                    bold_text = f'<strong>{text_to_bold}</strong>'
                    formated_text = paragraph[:span['start']] + bold_text + paragraph[span['end']:]
                elif span['type'] == 'em':
                    paragraph = formated_text
                    text_to_italicize = paragraph[span['start']:span['end']]
                    italicized_text = f'<em>{text_to_italicize}</em>'
                    formated_text = paragraph[:span['start']] + italicized_text + paragraph[span['end']:]
        elif len(text_data['spans']) > 1:
            prev_start_idx = 0
            prev_end_idx = 0
            for i, span in enumerate(text_data['spans']):
                substring = orginal_text[span['start']:span['end']]
                if i > 0 and text_format_is_subset(span, text_data['spans'][i - 1]):
                    # start checking from previous start position
                    start_idx = formated_text.find(substring, prev_start_idx)
                    end_idx = start_idx + len(substring)
                else:
                    # start checking from previous end position
                    start_idx = formated_text.find(substring, prev_end_idx)
                    end_idx = start_idx + len(substring)

                if span['type'] == 'hyperlink':
                    paragraph = formated_text
                    link_text = paragraph[start_idx:end_idx]
                    html_link = f'<a href="{span["data"]["url"]}">{link_text}</a>'
                    formated_text = paragraph[:start_idx] + html_link + paragraph[end_idx:]
                    prev_start_idx = start_idx
                    prev_end_idx = end_idx
                elif span['type'] == 'strong':
                    paragraph = formated_text
                    text_to_bold = paragraph[start_idx:end_idx]
                    bold_text = f'<strong>{text_to_bold}</strong>'
                    formated_text = paragraph[:start_idx] + bold_text + paragraph[end_idx:]
                    prev_start_idx = start_idx
                    prev_end_idx = end_idx
                elif span['type'] == 'em':
                    paragraph = formated_text
                    text_to_italicize = paragraph[start_idx:end_idx]
                    italicized_text = f'<em>{text_to_italicize}</em>'
                    formated_text = paragraph[:start_idx] + italicized_text + paragraph[end_idx:]
                    prev_start_idx = start_idx
                    prev_end_idx = end_idx
    return formated_text


def aggregate_image_slider_data(data=[]):
    slides = []
    for slide in data:
        if slide.get('image'):
            slides.append({
                'imageUrl': slide['image'].get('url') if slide['image'] else None,
                'title': slide['title'][0]['text'] if slide['title'] else None,
                'description': aggregate_text_data(slide['description']) if slide['description'] else None,
                'audio': aggregate_media_data(slide['audio']) if slide.get('audio') else None,
            })
    if len(slides) < 1:
        return None
    return slides


def aggregate_highlight_link(data):
    if 'type' in data and data['type'] == 'Link.web':
        html_link = f'<a href="{data["url"]}">{data["url"]}</a>'
    else:
        html_link = data["url"]
    return html_link


def aggregate_question_options(data, page_content=None):
    list_of_options = []
    for option in data:
        if len(option['options']) == 0:
            pass
        elif len(option['options']) > 1:
            # Here options are listed in a single field as separate paragraphs on prismic
            # and then split into separate options in the backend.
            # This is because options don't have follow up questions
            for item in option['options']:
                list_of_options.append({
                    'option': item['text'],
                    # TODO: add value after getting solution for translations
                    'description': None,
                    'followUpQuestion': None,
                })
        else:
            # Here each option is a separate field on prismic as it has follow up question related fields
            list_of_options.append({
                'option': option['options'][0]['text'] if option.get('options') else None,
                'description': add_spans(option['option_description'][0]) if option.get('option_description')
                else None,
                'followUpQuestion': {
                    'key': option['follow_up_question_key'] if option.get('follow_up_question_key') else None,
                    'question': option['follow_up_question'] if option.get('follow_up_question') else None,
                    'questionType': option['follow_up_question_type'] if option.get('follow_up_question_type')
                    else None,
                    'questionLink': option['follow_up_question_link']['url'] if option.get('follow_up_question_link')
                    and option['follow_up_question_link']['link_type'] == 'Web' else None,
                    'isRequired': option['is_required'] if option.get('is_required') else None,
                    'displayquestion': option['display_followup_question'] if option.get('display_followup_question')
                    else False,
                    'options': get_follow_up_question_options(
                        option['follow_up_question_options'],
                        option['follow_up_question_key'] if option.get('follow_up_question_key') else None,
                        page_content
                    ) if option.get('follow_up_question_options') else None,
                } if option.get('follow_up_question') else None,
            })
    return list_of_options


def get_follow_up_question_options(options_list, follow_up_question_key, page_content):
    list_of_options = []
    for option in options_list:
        list_of_options.append({
            'option': option['text'],
            # TODO: add value after getting solution for translations
            'description': None,
            'secondFollowUpQuestion': get_second_follow_up_question(
                option['text'], follow_up_question_key, page_content)
        })
    return list_of_options


def get_second_follow_up_question(option_text, follow_up_question_key, doc_data):
    if doc_data is None:
        return None

    qtn = next((item for item in doc_data if item['slice_type'] == 'second_followup_question' and
                item['primary']['follow_up_question_key'] == follow_up_question_key and
                item['primary']['follow_up_question_option'] == option_text), None)
    if qtn:
        second_followup_qtn_options = []
        if qtn['primary'].get('second_follow_up_question_options'):
            for option in qtn['primary']['second_follow_up_question_options']:
                second_followup_qtn_options.append({
                    'option': option['text'] if option.get('text') else None,
                    'description': None,
                })
        return {
            'key': qtn['primary']['second_follow_up_question_key'] if
            qtn['primary'].get('second_follow_up_question_key') else None,
            'question': qtn['primary']['second_follow_up_question'] if
            qtn['primary'].get('second_follow_up_question') else None,
            'questionType': qtn['primary']['second_follow_up_question_type'] if
            qtn['primary'].get('second_follow_up_question_type') else None,
            'questionLink': qtn['primary']['second_follow_up_question_link']['url'] if
            qtn['primary'].get('second_follow_up_question_link')
            and qtn['primary']['second_follow_up_question_link']['link_type'] == 'Web' else None,
            'isRequired': qtn['primary']['is_second_follow_up_required'] if
            qtn['primary'].get('is_second_follow_up_required') else None,
            'displayquestion': qtn['primary']['display_second_followup_question'] if
            qtn['primary'].get('display_second_followup_question') else False,
            'options': second_followup_qtn_options
        }
    return None


def aggregate_document_link(data):
    try:
        if data['link_type'] != 'Document' or data['isBroken']:
            return None
        return data if data else None
    except Exception as error:
        print(f'Could not aggregate document link data. {error}')
        return None


def aggregate_theme_name(data):
    if not data or not isinstance(data, str):
        raise Exception(f'Could not aggregate theme name of value: {data}.')
        return ''
    to_lower_case = data.lower()
    remove_spaces = to_lower_case.replace(' ', '_')
    return remove_spaces


def aggregate_lists(data, layout, native_page=False):
    try:
        items = []
        if not data or len(data) == 0:
            return []

        if layout == 'grid':
            i = 0
            while i < len(data):
                row = []
                icon = data[i]['icon'].get('url') if data[i].get('icon') else None
                label = data[i]['label'][0]['text'] if data[i].get('label') else None
                navigation_page = data[i]['navigation_page'] if data[i].get('navigation_page') else None
                page = None
                if data[i].get('page'):
                    page = data[i]['page'] if native_page else aggregate_document_link(data[i]['page'])
                row.append({
                    'icon': icon,
                    'label': label,
                    'navigationPage': navigation_page,
                    'page': page,
                })
                i += 1
                if i < len(data):
                    page_details = None
                    if data[i].get('page'):
                        page_details = data[i]['page']if native_page else aggregate_document_link(data[i]['page'])
                    row.append({
                        'icon': data[i]['icon'].get('url') if data[i].get('icon') else None,
                        'label': data[i]['label'][0]['text'] if data[i].get('label') else None,
                        'navigationPage': data[i]['navigation_page'] if data[i].get('navigation_page')
                        else None,
                        'page': page_details,
                    })
                items.append(row)
                i += 1

        elif layout == 'home_tabs' or layout == 'navigation_tabs':
            for item in data:
                try:
                    page = aggregate_document_link(item['page']) if item.get('page') else None
                    if page and page.get('uid'):
                        page['uid'] = page['uid'].split('.')[0]
                    items.append({
                        'icon': item['icon'].get('url') if item.get('icon') else None,
                        'label': item['label'][0]['text'] if item.get('label') else None,
                        'theme': aggregate_theme_name(item['theme']) if item.get('theme') else None,
                        'illustration': item['illustration'].get('url')
                        if item.get('illustration') else None,
                        'navigationPage': item['navigation_page'] if item.get('navigation_page') else None,
                        'page': page,
                        'welcomeText': item['welcome_text'] if item.get('welcome_text') else None,
                        'welcomeTextAudio': aggregate_media_data(item['welcome_text_audio'])
                        if item.get('welcome_text_audio') else None,
                    })
                except Exception as error:
                    raise Exception(f'Could not aggregate slice data of list {layout}', error)

        else:
            for item in data:
                page = aggregate_document_link(item['page']) if item.get('page') else None
                items.append({
                    'icon': item['icon'].get('url') if item.get('icon') else None,
                    'label': item['label'][0]['text'] if item.get('label') else None,
                    'navigationPage': item['navigation_page'] if item.get('navigation_page') else None,
                    'page': page,
                })

        return items

    except Exception as error:
        print(f'Could not aggregate lists data. {error}')
        return None


def aggregate_non_click_lists(data):
    items = []
    for item in data:
        items.append({
            'icon': item['icon'].get('url') if item.get('icon') else None,
            'description': aggregate_text_data(item['description']) if item.get('description') else None,
        })
    return items


def aggregate_drop_down_data(data):
    accordions = []
    for item in data['items']:
        accordions.append({
            'title': item['title'][0]['text'] if item.get('title') else None,
            'titleAudio': aggregate_media_data(item['dd_title_audio']) if item.get('dd_title_audio') else None,
            'description': aggregate_text_data(item['description']) if item.get('description') else None,
            'showDescription': False,
        })
    return accordions


def format_case_study(page, sub_chapter=None, item=None):
    case_study = {
        'uid': page['uid'],
        'id': page['id'],
        'language': page['lang'],
        'type': 'case_study',
        'image': aggregate_media_data(page['data'].get('cover_image')) if page['data'].get('cover_image') else None,
        'pageTitle': page['data'].get('page_title')[0].get('text') if page['data'].get('page_title')
        else 'Title',
        'description': [],
        'pageTitleAudio': aggregate_media_data(page['data'].get('title_audio'))
        if page['data'].get('title_audio') else None,
        'pageContent': [],
        'subChapter': sub_chapter,
        'pageIcon': aggregate_media_data(page['data'].get('page_icon'))
        if page['data'].get('page_icon') else None,
        'analyticsEventName': page['data'].get('analytics_event_name')
        if page['data'].get('analytics_event_name') else None,
    }

    if 'body' in page['data'] and page['data']['body']:
        slices = page['data']['body']

        for el in slices:
            slice_data = format_common_slice_data(el)
            if slice_data['type'] == 'text_area' and not case_study['description']:
                case_study['description'] = slice_data['description']
            case_study['pageContent'].append(slice_data)

    return case_study


def format_common_slice_data(item, pagesList=None, page=None, page_content=None):
    try:
        if item['slice_type'] == 'video_area':
            return {
                'type': 'video',
                'mediaData': aggregate_media_data(item['primary']['video_link'])
                if item['primary'].get('video_link') else None,
                'thumbnail': aggregate_media_data(item['primary']['thumbnail'])
                if item['primary'].get('thumbnail') else None,
            }
        elif item['slice_type'] == 'audio':
            return {
                'type': 'audio',
                'title': item['primary']['audio_title'][0]['text']
                if item['primary'].get('audio_title') else None,
                'description': aggregate_text_data(item['primary']['audio_description'])
                if item['primary'].get('audio_description') else None,
                'mediaData': aggregate_media_data(item['primary']['audio_link'])
                if item['primary'].get('audio_link') else None,
            }
        elif item['slice_type'] == 'single_image':
            return {
                'type': 'image',
                'title': item['primary']['title'][0]['text'] if item['primary'].get('title')
                else None,
                'mediaData': aggregate_media_data(item['primary']['single_image'])
                if item['primary'].get('single_image') else None,
            }
        elif item['slice_type'] == 'images_slider':
            return {
                'type': 'images_slider',
                'sliderContent': aggregate_image_slider_data(item['items']),
            }
        elif 'heading' in item['slice_type']:
            return {
                'type': item['slice_type'],
                'text': item['primary']['heading'][0]['text'] if item['primary'].get('heading') else None,
                'headingAudio': aggregate_media_data(item['primary']['heading_audio']) if item['primary'].get(
                    'heading_audio') else None,
            }
        elif item['slice_type'] == 'text_area':
            return {
                'type': 'text_area',
                'title': item['primary']['h2_title_area'][0]['text']
                if item['primary'].get('h2_title_area') else None,
                'description': aggregate_text_data(item['primary']['text_area'])
                if item['primary'].get('text_area') else None,
                'contentAudio': aggregate_media_data(item['primary']['content_audio']) if item['primary'].get(
                    'content_audio') else None,
                'identifier': item['primary'].get('identifier', None),
            }
        elif item['slice_type'] == 'highlighted_link':
            return {
                'type': 'highlighted_link',
                'icon': aggregate_media_data(item['primary']['link_icon'])
                if item['primary'].get('link_icon') else None,
                'description': aggregate_text_data(item['primary']['link_description'])
                if item['primary'].get('link_description') else None,
                'link': aggregate_highlight_link(item['primary']['highlighted_link'])
                if item['primary'].get('highlighted_link') else None,
            }
        elif item['slice_type'] == 'warning_box':
            return {
                'type': 'warning_box',
                'icon': aggregate_media_data(item['primary']['warning_icon'])
                if item['primary'].get('warning_icon') else None,
                'description': aggregate_text_data(item['primary']['warning_text'])
                if item['primary'].get('warning_text') else None,
                'title': item['primary']['warning_title'][0]['text']
                if item['primary'].get('warning_title') else None,
            }
        elif item['slice_type'] == 'questions':
            return {
                'type': 'questions',
                'question': item['primary']['question'][0]['text']
                if item['primary'].get('question') else None,
                'questionType': item['primary']['question_type'] if item['primary'].get('question_type') else None,
                'key': item['primary']['question_key'] if item['primary'].get('question_key') else None,
                'questionAudio': aggregate_media_data(item['primary']['question_audio']) if item['primary'].get(
                    'question_audio') else None,
                'questionLink': item['primary']['question_link']['url'] if item['primary']['question_link']
                and item['primary']['question_link']['link_type'] == 'Web' else None,
                'isRequired': item['primary']['is_required'] if item['primary'].get('is_required') else None,
                'displayquestion': item['primary']['display_question'] if item['primary'].get('display_question')
                else False,
                'options': aggregate_question_options(item['items'], page_content) if item.get('items') else None,
            }
        elif item['slice_type'] == 'list':
            layout = item['primary']['layout'].lower() if item['primary'].get('layout') else 'grid'
            return {
                'type': 'list',
                'layout': layout,
                'list': aggregate_lists(item['items'], layout, True) if item.get('items') else None,
            }
        elif item['slice_type'] == 'clickable_list':
            layout = item['primary']['layout'].lower() if item['primary'].get('layout') else 'flow'
            return {
                'type': 'clickable_list',
                'layout': layout,
                'list': aggregate_lists(item['items'], layout) if item.get('items') else None,
            }
        elif item['slice_type'] == 'non-clickable-list':
            return {
                'type': 'non-clickable-list',
                'heading': item['primary']['heading'][0]['text'] if item['primary'].get('heading')
                else None,
                'list': aggregate_non_click_lists(item['items']) if item.get('items') else None,
            }
        elif item['slice_type'] == 'drop_down_content':
            return {
                'type': 'drop_down_content',
                'data': aggregate_drop_down_data(item),
            }
        elif item['slice_type'] == 'case_study':
            case_study_uid = item['primary']['link']['uid'] if item['primary']['link'] else None
            case_study = next((e for e in pagesList if e['uid'] == case_study_uid), None) if case_study_uid else None
            result = format_case_study(case_study, page['uid'], item) if case_study else None
            return result
        else:
            return None
    except Exception as e:
        print(f'Could not aggregate slice data {item["slice_type"]}: {e}')
        return None
