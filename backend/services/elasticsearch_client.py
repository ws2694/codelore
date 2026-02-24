from elasticsearch import Elasticsearch

from backend.config import get_settings

_client: Elasticsearch | None = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Elasticsearch(
            settings.es_url,
            api_key=settings.es_api_key,
        )
    return _client
