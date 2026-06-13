import os
import sys
import torch
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.env_loader import load_env

load_env()

# Overridable so tests can target a throwaway collection instead of production.
TEXT_COLLECTION = os.getenv("HL_TEXT_COLLECTION", "heritage_lens_text")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    from llama_index.core import VectorStoreIndex
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings
except ImportError:
    print("WARNING: Missing required dependencies. To run this script, please install:")
    print("pip install llama-index llama-index-vector-stores-qdrant qdrant-client pypdf llama-index-embeddings-huggingface")

def get_retriever():
    Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    client = QdrantClient(url="http://localhost:6333")
    vector_store = QdrantVectorStore(client=client, collection_name=TEXT_COLLECTION)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model,
    )
    return index

def retrieve_chunks(query: str, top_k: int = 15) -> list:
    """
    Query the vector DB and strictly extract text and the required metadata schema.
    Uses balanced retrieval across all source PDFs to prevent any single document
    from dominating the context.
    """
    index = get_retriever()
    
    # Detect all unique PDFs in the database
    try:
        client = QdrantClient(url="http://localhost:6333")
        scroll_results, _ = client.scroll(
            collection_name=TEXT_COLLECTION,
            with_payload=True,
            limit=10000,
        )
        source_names = set(
            p.payload.get("source_name")
            for p in scroll_results
            if p.payload and p.payload.get("source_name")
        )
        source_list = sorted(source_names)
    except Exception as e:
        print(f"Error fetching source names from database: {e}")
        source_list = []
        
    if len(source_list) <= 1:
        # Fallback to standard global query if only one or no PDFs are found in the DB
        print("Fallback to standard global retrieval.")
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
    else:
        # Balanced retrieval
        from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
        print(f"Balanced retrieval active across {len(source_list)} sources: {source_list}")
        
        # Determine number of chunks to fetch per source
        per_source_k = max(5, (top_k + len(source_list) - 1) // len(source_list))
        
        all_nodes = []
        for src_name in source_list:
            try:
                filters = MetadataFilters(
                    filters=[MetadataFilter(key="source_name", value=src_name)]
                )
                retriever = index.as_retriever(similarity_top_k=per_source_k, filters=filters)
                nodes = retriever.retrieve(query)
                all_nodes.extend(nodes)
            except Exception as e:
                print(f"Error retrieving from source {src_name}: {e}")
                
        # Sort merged nodes by score descending (handling None scores gracefully)
        nodes = sorted(all_nodes, key=lambda x: x.score if x.score is not None else 0.0, reverse=True)
        
    results = []
    # Deduplicate nodes by text to ensure uniqueness, keeping the highest score
    seen_texts = set()
    for node_with_score in nodes:
        node = node_with_score.node
        if node.text in seen_texts:
            continue
        seen_texts.add(node.text)
        
        results.append({
            "text": node.text,
            "metadata": node.metadata,
            "score": node_with_score.score
        })
        if len(results) >= top_k:
            break
            
    return results

_siglip_processor = None
_siglip_model = None

def _get_siglip():
    global _siglip_processor, _siglip_model
    if _siglip_processor is None:
        from transformers import AutoProcessor, SiglipModel
        _siglip_processor = AutoProcessor.from_pretrained("google/siglip2-base-patch16-224")
        _siglip_model = SiglipModel.from_pretrained("google/siglip2-base-patch16-224")
        _siglip_model.eval()
    return _siglip_processor, _siglip_model


def retrieve_images(query: str, top_k: int = 3, source_filter: str = None, media_type: str = None) -> list:
    """
    Cross-modal search: text query → ranked image/video results from Qdrant.
    media_type: None (all), 'pdf_image', 'uploaded_image', or 'video_frame'
    """
    processor, model = _get_siglip()
    inputs = processor(text=[query], return_tensors="pt", padding="max_length")
    with torch.no_grad():
        outputs = model.text_model(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
        )
        features = outputs.pooler_output  # (1, 768)
        features = features / features.norm(dim=-1, keepdim=True)
    query_vec = features[0].cpu().numpy().tolist()

    conditions = []
    if source_filter:
        conditions.append(FieldCondition(key="source_name", match=MatchValue(value=source_filter)))
    if media_type:
        conditions.append(FieldCondition(key="media_type", match=MatchValue(value=media_type)))
    qdrant_filter = Filter(must=conditions) if conditions else None

    client = QdrantClient(url="http://localhost:6333")
    results = client.query_points(
        collection_name="heritage_lens_images",
        query=query_vec,
        query_filter=qdrant_filter,
        limit=top_k,
        with_payload=True,
    )
    return [
        {"image_path": r.payload["image_path"], "metadata": r.payload, "score": r.score}
        for r in results.points
    ]


if __name__ == "__main__":
    # Test execution
    chunks = retrieve_chunks("What was the ritual function of obsidian at Olmec ceremonial sites?")
    for c in chunks:
        print(c["metadata"])
