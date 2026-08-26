import logging
import time

import requests
from decouple import config


logger = logging.getLogger(__name__)


class StrapiContentService:
    def __init__(self):
        self.base_url = config("STRAPI_BASE_URL").rstrip("/")
        self.api_base_url = f"{self.base_url}/api"
        self.api_token = config("STRAPI_API_TOKEN")
        self.timeout = 30  # seconds
        self.max_retries = 3
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            }
        )

    def get_all_documents(self, collection_name='ikan', params=None):
        url = f"{self.api_base_url}/{collection_name}"
        request_params = dict(params or {})
        custom_type = request_params.pop("custom_type", None)
        if custom_type:
            request_params["filters[custom_type][$eq]"] = custom_type

        response = self._get(url, params=request_params)
        if response is None:
            return None
        return response.json()

    def get_document(self, payload):
        collection_name = payload.get("collection_name")
        document_id = payload.get("document_id")
        url = f"{self.api_base_url}/{collection_name}/{document_id}"
        response = self._get(url, params=payload.get("params"))
        if response is None:
            return None
        return response.json()

    def _get(self, url, params=None):
        attempt = 0

        while attempt < self.max_retries:
            try:
                response = self.session.get(url, params=params or {}, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout as error:
                attempt += 1
                logger.warning(
                    "Timeout fetching Strapi URL %s (attempt %s/%s)",
                    url,
                    attempt,
                    self.max_retries,
                )
                if attempt >= self.max_retries:
                    logger.error(
                        "Max retries reached for Strapi URL %s after timeout: %s",
                        url,
                        error,
                    )
                    return None
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as error:
                logger.error("Request to Strapi failed for URL %s: %s", url, error)
                return None
