import chromadb
from chromadb.config import Settings
import os

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

_client: chromadb.PersistentClient | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_niche_spots_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="niche_spots",
        metadata={"hnsw:space": "cosine"},
    )


def get_itineraries_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="itineraries",
        metadata={"hnsw:space": "cosine"},
    )
