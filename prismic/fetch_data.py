from typing_extensions import dataclass_transform
from xml.dom.pulldom import parseString
import requests
from rest_framework import exceptions
from decouple import config
import requests


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
        url = self.build_url(type='doc_search')
        for language in self.languages:
            lang_id = language['id']
            lang_url = f'{url}&lang={lang_id}'
            self.get_documents(lang_url)
    
    def get_documents(self, url, lang_code):
        req = requests.get(url)
        req.raise_for_status()
        docs_data = req.json()
        agg_data = self.aggr_data(docs_data)  
        return agg_data

    def aggr_data(self, data):
        aggregated_data = {}
        for item in data['results']:
            if item == 'form_questions':

        def agg_common_text(self, data):
            pass

        def agg_form_questions(self):
            pass
