from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import socket

from trafilatura import fetch_url, extract

def get_local_ip() -> str:
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        soc.connect(('8.8.8.8', 80))
        ip = soc.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        soc.close()

    return ip

@dataclass
class WebFetchResponse:
    url: str
    title: str
    author: str | None
    date: str | None
    content: str

class WebFetchProvider(ABC):
    @property
    def name(self):
        ...

    @abstractmethod
    def fetch(self, **kwargs) -> WebFetchResponse:
        ...

class WebFetchRegistry:
    _instance = None
    _engines = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def register(self, instance: WebFetchProvider):
        self._engines[instance.name] = instance

    @property
    def extractors(self):
        return [(ext[0], ext[1]) for ext in self._engines.items()]

    def get(self, name: str):
        if name in self._engines:
            return self._engines[name]

        return f"Error: {name} is not a valid web fetch engine."

class TrafilaturaWebFetch(WebFetchProvider):
    @property
    def name(self):
        return "trafilatura"

    def fetch(self, **kwargs):
        if not kwargs.get('url'):
            return 'URL not found'

        url = kwargs['url']

        if '127.0.0.1' in url or get_local_ip() in url:
            return 'URL not permitted'

        html_page = fetch_url(url)
        if not html_page:
            return f"page from \"{url}\" not found"

        extracted_content = extract(
            html_page,
            with_metadata=True,
            output_format='json',
            include_comments=False
        )
        if not extracted_content:
            return f"Extraction of \"{url}\" has failed"

        content = json.loads(extracted_content)

        return WebFetchResponse(
            url=url,
            title=content['title'],
            author=content['author'],
            date=content['date'],
            content=content['raw_text']
        )
