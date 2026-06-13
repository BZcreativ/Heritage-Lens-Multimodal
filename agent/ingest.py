import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.env_loader import load_env

load_env()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import VectorParams, Distance
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Document
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings
except ImportError:
    print("WARNING: Missing required dependencies. To run this script, please install:")
    print("pip install llama-index llama-index-vector-stores-qdrant qdrant-client pypdf llama-index-embeddings-huggingface")

try:
    Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
except NameError:
    pass

# The non-negotiable metadata mapping for our specific corpora.
# This JSON projection maps directly to the Layer 3 logic inside 'agent/generator.py'
METADATA_MAPPING = {
    "Formazione della Citta in Mesoamerica.pdf": {
        "source_type": "thesis",
        "institution": "Italian University Press",
        "cultural_perspective": "western_academic",
        "language_of_origin": "italian"
    },
    "MESOAMERICA TRA SEGNO E SIGNIFICATO.pdf": {
        "source_type": "book",
        "institution": "Centro Studi Americanistici - Circolo Amerindiano",
        "cultural_perspective": "western_academic",
        "language_of_origin": "italian"
    }
}

DEFAULT_METADATA = {
    "source_type": "unknown",
    "institution": "unknown",
    "cultural_perspective": "unknown",
    "language_of_origin": "unknown"
}

def load_documents_with_metadata(data_dir: str):
    """
    Load PDFs and forcefully inject strict metadata JSON to every resulting LlamaIndex chunk.
    This fulfills the non-negotiable requirement for Layer 3 (Epistemic Transparency report).
    """
    directory = Path(data_dir)
    documents = []

    if not directory.exists() or not directory.is_dir():
        print(f"Data directory '{data_dir}' not found.")
        return documents

    for filepath in directory.glob("*.pdf"):
        filename = filepath.name
        # Provide exact metadata mapping, or default if novel PDF
        metadata_dict = METADATA_MAPPING.get(filename, DEFAULT_METADATA.copy())
        
        # Include source_name so our Layer 2 UI component can cite it comfortably
        metadata_dict["source_name"] = filename

        if "Formazione della Citta" in filename:
            metadata_dict["author"] = "Larissa Terranova"
        elif "Mesoamerica tra Segno e Significato" in filename or "MESOAMERICA TRA SEGNO E SIGNIFICATO" in filename:
            metadata_dict["author"] = "Romolo Santoni"

        print(f"Parsing '{filename}' and injecting dict: {metadata_dict}")
        
        from pypdf import PdfReader
        try:
            reader = PdfReader(str(filepath))
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                page_meta = metadata_dict.copy()
                page_meta["page_number"] = str(i + 1)
                
                doc = Document(text=text, metadata=page_meta)
                documents.append(doc)
        except Exception as e:
            print(f"Error parsing {filename} with pypdf: {e}")
            
    return documents

def initialize_vector_db():
    print("=== INITIALIZING QDRANT VECTOR DATABASE ===")

    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_dir = os.path.join(workspace_dir, "data", "corpus")

    client = QdrantClient(url="http://localhost:6333")
    client.delete_collection("heritage_lens_text")
    client.create_collection(
        "heritage_lens_text",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("Qdrant collection 'heritage_lens_text' recreated.")

    vector_store = QdrantVectorStore(client=client, collection_name="heritage_lens_text")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print(f"Scanning for PDF corpora in: {corpus_dir}")
    documents = load_documents_with_metadata(corpus_dir)
    
    if not documents:
        print("No documents found. Nothing to ingest.")
        return
        
    print(f"Successfully loaded {len(documents)} raw document pages/fragments.")
    print("Chunking documents (chunk_size=512, overlap=50) and embedding into Vector DB...")
    
    # Node splitting parameters to ensure chunks are granular enough for robust retrieval
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)
    
    print(f"Created {len(nodes)} discrete chunks. Generating embeddings...")
    
    index = VectorStoreIndex(
        nodes, 
        storage_context=storage_context,
        show_progress=True
    )
    
    print(f"=== TEXT INDEXING COMPLETE: {len(nodes)} chunks ingested. ===")

    from agent.video_ingest import index_videos_in_corpus
    from agent.image_ingest import (
        index_images_from_corpus, index_standalone_images,
        index_video_frames, VIDEO_EXTS,
    )
    index_images_from_corpus(corpus_dir, client)
    index_standalone_images(corpus_dir, client)
    for video_path in Path(corpus_dir).iterdir():
        if video_path.suffix.lower() in VIDEO_EXTS:
            index_video_frames(str(video_path), client)

    # ── Video text indexing (audio transcripts + visual captions/OCR) ──
    print("=== INDEXING VIDEO TEXT DERIVATIVES ===")
    index_videos_in_corpus(corpus_dir, client, index_audio=True, index_visual=False)
    print("=== VIDEO TEXT INDEXING COMPLETE ===")

if __name__ == "__main__":
    initialize_vector_db()
