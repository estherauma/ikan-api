import requests
from decouple import config
from prismic.models import AggregatedContent, MessagingContent


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
            '''Aggregate form questions'''
            for question in form_data:
                key, label, question_type, displayquestion, help_text, options,\
                    options_translations = question['primary'].values()
                final_options_array = []
                if options is not None:
                    options = options.split(',')
                    option_list = []
                    for option in options:
                        # TODO: Leaving this for things entries we already have on prismic as a fall back.
                        # Once all are updated, we can remove this
                        new_options_dict = {"value": option, "label": option}
                        option_list.append(new_options_dict)
                        final_options_array = option_list

                if options_translations and options:
                    options_translations = options_translations.split(',')
                    final_options_array = [{"value": key, "label": value} for key, value
                                           in zip(options_translations, options)]
                question_data.append(
                    {
                        'key': key,
                        'label': label,
                        'question_type': question_type,
                        'displayquestion': displayquestion,
                        'help_text': help_text,
                        'options': final_options_array,
                    })
            return question_data

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

        for item in data['results']:
            if item['type'] == 'form_questions':
                page_data = {
                    'page_name': item['uid'],
                    'page_title': item['data']['page_title'],
                    'last_updated': item['last_publication_date'],
                    'form_questions': agg_form_questions(item['data']['body'])
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
            result = self.aggregate_content(content_to_agg)
            return result

        elif content_to_agg and saved_agg_content:
            agg_content = self.aggregate_content(content_to_agg)
            if bool(agg_content):
                final_data = None
                for lang in agg_content:
                    updated_lang_data = agg_content[lang]
                    saved_lang_data = saved_agg_content.get(lang, None)
                    if saved_lang_data:
                        for doc in updated_lang_data:
                            new_doc_id = doc["id"]
                            # existing document index
                            index = next(
                                (i for i, item in enumerate(saved_lang_data)
                                    if item["id"] == new_doc_id), None)
                            if index is None:
                                saved_lang_data.append(doc)
                            else:
                                saved_lang_data[index] = doc

                        new_lang_data = {}
                        new_lang_data[lang] = saved_lang_data
                        final_data = {**saved_agg_content, **new_lang_data}
                    else:
                        final_data = saved_agg_content
                        final_data[lang] = updated_lang_data
                return final_data
            else:
                return None

    def aggregate_content(self, data):
        agg_data = {}

        for item in data:
            if item['type'] == 'message':
                page_data = {
                    'id': item['id'],
                    'page_name': item['uid'],
                    'type': item['type'],
                    'language': item['lang'],
                    'pageTitle': item['data'].get('page_title')[0].get('text') if item['data'].get('page_title')
                    else 'Message Title',
                    'pageTitleAudio': aggregate_media_data(item['data'].get('title_audio'))
                    if item['data'].get('title_audio') else None,
                    'pageIcon': aggregate_media_data(item['data'].get('page_icon'))
                    if item['data'].get('page_icon') else None,
                    'userRole': item['data'].get('user_role') if item['data'].get('user_role') else None,
                    'pageContent': [],
                }
                if 'body' in item['data'] and item['data']['body']:
                    page_content = item['data']['body']
                    for data in page_content:
                        slice_data = format_common_slice_data(data, page_data, item)
                        page_data['pageContent'].append(slice_data)

                if agg_data.get(item['lang']) is None:
                    agg_data[item['lang']] = [page_data]
                else:
                    agg_data[item['lang']].append(page_data)
        return agg_data


def aggregate_media_data(data):
    if not data:
        return None
    aggregated_media_data = {}
    if not data.get('type'):
        return {}
    media_type = data.get('type')
    if media_type == 'Link.file':
        aggregated_media_data = data.get('file')
    elif media_type == 'Link.web':
        aggregated_media_data = {
            'name': 'unknown',
            'kind': 'web',
            'url': data.get('url'),
            'size': 'unknown'
        }
    elif media_type == 'Image':
        aggregated_media_data = {
            'name': data.get('main').get('alt', 'unknown'),
            'kind': 'image',
            'url': data.get('main').get('url'),
            'dimensions': data.get('main').get('dimensions')
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
    if not text_data:
        return None
    formated_text = text_data.get('text', '')
    if (text_data['type'] in ['paragraph', 'list-item', 'o-list-item']) and text_data.get('spans'):
        text_data['spans'].reverse()
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
    return formated_text


def aggregate_image_slider_data(data=[]):
    slides = []
    for slide in data:
        if slide.get('image'):
            slides.append({
                'imageUrl': slide['image'].get('main').get('url') if slide['image'] else None,
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


def aggregate_question_options(data):
    list_of_options = []
    for option in data:
        list_of_options.append({
            'option': option['options'][0]['text'] if option.get('options') else None,
            'description': add_spans(option['option_description'][0]) if option.get('option_description')
            else None,
            'followUpQuestion': {
                'key': option['follow_up_question_key'] if option.get('follow_up_question_key') else None,
                'question': option['follow_up_question'] if option.get('follow_up_question') else None,
                'questionType': option['follow_up_question_type'] if option.get('follow_up_question_type')
                else None,
                'options': option['follow_up_question_options'] if option.get('follow_up_question_options')
                else None,
            } if option.get('follow_up_question') else None,
        })
    return list_of_options


def aggregate_document_link(data):
    try:
        if data['type'] != 'Link.document' or data['value']['isBroken']:
            return None
        return data['value']['document'] if data['value']['document'] else None
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
                icon = data[i]['icon'].get('main').get('url') if data[i].get('icon') else None
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
                        'icon': data[i]['icon'].get('main').get('url') if data[i].get('icon') else None,
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
                        'icon': item['icon'].get('main').get('url') if item.get('icon') else None,
                        'label': item['label'][0]['text'] if item.get('label') else None,
                        'theme': aggregate_theme_name(item['theme']) if item.get('theme') else None,
                        'illustration': item['illustration'].get('main').get('url')
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
                    'icon': item['icon'].get('main').get('url') if item.get('icon') else None,
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
            'icon': item['icon'].get('main').get('url') if item.get('icon') else None,
            'description': aggregate_text_data(item['description']) if item.get('description') else None,
        })
    return items


def aggregate_drop_down_data(data):
    accordions = []
    for item in data['repeat']:
        accordions.append({
            'title': item['title'][0]['text'] if item.get('title') else None,
            'titleAudio': aggregate_media_data(item['dd_title_audio']) if item.get('dd_title_audio') else None,
            'description': aggregate_text_data(item['description']) if item.get('description') else None,
            'showDescription': False,
        })
    return accordions


def format_common_slice_data(item, pagesList=None, page=None):
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
                'sliderContent': aggregate_image_slider_data(item['repeat']),
            }
        elif item['slice_type'] == 'text_area':
            return {
                'type': 'text_area',
                'title': item['primary']['h2_title_area'][0]['text']
                if item['primary'].get('h2_title_area') else None,
                'description': aggregate_text_data(item['primary']['text_area'])
                if item['primary'].get('text_area') else None,
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
                'key': item['primary']['question_key'] if item['primary'].get('question_key')
                else None,
                'options': aggregate_question_options(item['repeat']) if item.get('repeat') else None,
            }
        elif item['slice_type'] == 'list':
            layout = item['primary']['layout'].lower() if item['primary'].get('layout') else 'grid'
            return {
                'type': 'list',
                'layout': layout,
                'list': aggregate_lists(item['repeat'], layout, True) if item.get('repeat') else None,
            }
        elif item['slice_type'] == 'clickable_list':
            layout = item['primary']['layout'].lower() if item['primary'].get('layout') else 'flow'
            return {
                'type': 'clickable_list',
                'layout': layout,
                'list': aggregate_lists(item['repeat'], layout) if item.get('repeat') else None,
            }
        elif item['slice_type'] == 'non-clickable-list':
            return {
                'type': 'non-clickable-list',
                'heading': item['primary']['heading'][0]['text'] if item['primary'].get('heading')
                else None,
                'list': aggregate_non_click_lists(item['repeat']) if item.get('repeat') else None,
            }
        elif item['slice_type'] == 'drop_down_content':
            return {
                'type': 'drop_down_content',
                'data': aggregate_drop_down_data(item),
            }
        else:
            return None
    except Exception as e:
        print(f'Could not aggregate slice data {item["slice_type"]}: {e}')
        return None
