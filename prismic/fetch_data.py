import requests
from rest_framework import exceptions
from decouple import config
import requests
from prismic.models import AggregatedContent


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
                f'access_token={self.access_token}'

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
            documents[lang_id] =  self.get_documents(url=lang_url)
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
                key, label, question_type, displayquestion, help_text, options = question['primary'].values()
                if options != None:
                    options = options.split(',')
                question_data.append(
                    {
                        'key':key, 
                        'label': label, 
                        'question_type': question_type,
                        'displayquestion': displayquestion,
                        'help_text': help_text,
                        'options': options 
                    })
            return question_data
        
        def agg_common_text(common_text_data):
            '''Aggregrate common text'''
            aggr_common_content = []
            for x in common_text_data:
                aggr_common_content.append(x['primary'])
            return aggr_common_content

        def agg_side_menu(menu_data):
            return [ menu['primary'] for menu in menu_data]
        
        def agg_intro_content(intro_data):
            return [ data['primary'] for data in intro_data]
        
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
