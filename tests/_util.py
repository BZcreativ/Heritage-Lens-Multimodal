"""Test isolation helpers.

Importing this module forces HL_TEXT_COLLECTION to a throwaway collection BEFORE
agent.video_ingest / agent.retriever are imported (they read the name at import
time), so tests never read or write the production heritage_lens_text data.
"""
import os

TEST_COLLECTION = "heritage_lens_text_pytest"
os.environ["HL_TEXT_COLLECTION"] = TEST_COLLECTION  # force; tests must never touch prod


def setup_collection(client):
    """Create a fresh, empty 384-dim COSINE test collection."""
    from qdrant_client.http.models import VectorParams, Distance
    try:
        client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    client.create_collection(
        TEST_COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )


def teardown_collection(client):
    """Drop the test collection."""
    try:
        client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
