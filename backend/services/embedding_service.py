from functools import lru_cache

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


@lru_cache(maxsize=256)
def embed_text(text: str) -> list[float]:
    """Embed text with LRU cache — same query string reuses the cached vector."""
    return get_model().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts).tolist()
