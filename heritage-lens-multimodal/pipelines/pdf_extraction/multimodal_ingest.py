"""
Multimodal PDF Ingestion Pipeline
Extracts text chunks and images from PDFs with CLIP embeddings and LlamaIndex indexing
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib
import json
from datetime import datetime
import yaml
from PIL import Image
import numpy as np


# Detect project root - works in both Docker and local environments
PROJECT_ROOT = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")

class MultimodalIngestPipeline:
    """Pipeline for ingesting PDFs with text and image extraction"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        # Load environment variables first
        self._load_env_file()

        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.config_path = str(config_full_path)

        # Import agents
        import sys
        sys.path.append(str(PROJECT_ROOT))
        from agents.vision.vision_agent import VisionAgent
        from agents.retrieval.multimodal_retrieval_agent import MultimodalRetrievalAgent

        self.vision_agent = VisionAgent(self.config_path)
        self.retrieval_agent = MultimodalRetrievalAgent(self.config_path)

        # Pipeline settings
        self.pipeline_config = self.config.get("data_pipeline", {})
        self.pdf_config = self.pipeline_config.get("pdf_extraction", {})
        self.metadata_config = self.pipeline_config.get("metadata", {})

        # Track processed PDFs
        self.processed_pdfs: Dict[str, Dict] = {}
        self._load_processed_cache()

        # Setup directories
        self.data_dir = PROJECT_ROOT / "data"
        self.extracted_images_dir = self.data_dir / "extracted_images"
        self.extracted_images_dir.mkdir(parents=True, exist_ok=True)

        # Document registry (lazy-loaded)
        self._document_registry = None

    def _load_env_file(self):
        """Load environment variables from .env file"""
        import os
        env_path = PROJECT_ROOT / "config" / ".env"
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        # Only set if not already set in environment
                        if key not in os.environ:
                            os.environ[key] = value

    def _load_processed_cache(self):
        """Load cache of processed PDFs"""
        cache_file = PROJECT_ROOT / "data" / "processed_pdfs.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                self.processed_pdfs = json.load(f)

    def _save_processed_cache(self):
        """Save cache of processed PDFs"""
        cache_file = PROJECT_ROOT / "data" / "processed_pdfs.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(self.processed_pdfs, f, indent=2)

    async def process_pdf(
        self,
        pdf_path: str,
        metadata: Dict = None,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process a PDF file - extract text chunks and images

        Args:
            pdf_path: Path to PDF file
            metadata: Optional metadata to attach
            force_reprocess: Reprocess even if already in cache

        Returns:
            Processing results with extracted content info
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {"status": "error", "message": f"PDF not found: {pdf_path}"}

        # Check if already processed
        file_hash = self._calculate_file_hash(pdf_file)
        if not force_reprocess and file_hash in self.processed_pdfs:
            return {
                "status": "cached",
                "message": "PDF already processed (use force_reprocess=True to reprocess)",
                "pdf_hash": file_hash,
                "previous_result": self.processed_pdfs[file_hash]
            }

        # Register/update document in registry for Archive Panel
        registry = self._get_document_registry()
        doc_record = registry.get_document(file_hash)
        if not doc_record:
            file_type = self._get_file_type(pdf_file.suffix)
            doc_record = registry.register_document(
                doc_id=file_hash,
                filename=pdf_file.name,
                filepath=str(pdf_file),
                file_size=pdf_file.stat().st_size,
                file_type=file_type,
                metadata=metadata
            )

        # Initialize results
        results = {
            "pdf_path": str(pdf_file),
            "pdf_hash": file_hash,
            "processed_at": datetime.now().isoformat(),
            "status": "processing",
            "text_chunks": [],
            "images_extracted": [],
            "errors": []
        }

        try:
            # Update status to indexing
            registry.update_status(file_hash, status="indexing")

            # Extract text and images
            extraction_result = await self._extract_pdf_content(pdf_file, metadata)

            # If no text found, try OCR (for image-based/scanned PDFs)
            if extraction_result["text_chunks_count"] == 0 and extraction_result["images_count"] == 0:
                print(f"No text extracted, attempting OCR for {pdf_file.name}...")
                from pipelines.pdf_extraction.ocr_extraction import extract_pdf_with_ocr
                extraction_result = await extract_pdf_with_ocr(
                    pdf_file,
                    self.extracted_images_dir,
                    metadata,
                    self._enrich_metadata,
                    self.metadata_config
                )

            results.update(extraction_result)

            # Update progress: chunks and images found
            registry.update_status(
                file_hash,
                status="indexing",
                chunks_total=len(results["text_chunks"]),
                images_extracted=len(results["images_extracted"])
            )

            # Index text chunks with LlamaIndex
            if results["text_chunks"]:
                await self._index_text_chunks_with_progress(results["text_chunks"], pdf_file.name, file_hash, registry)

            # Process images with CLIP
            if results["images_extracted"]:
                await self._process_images(results["images_extracted"])

            # Mark as successfully indexed
            registry.update_status(
                file_hash,
                status="indexed",
                chunks_indexed=len(results["text_chunks"]),
                images_extracted=len(results["images_extracted"])
            )
            results["status"] = "success"

        except Exception as e:
            error_msg = str(e)
            results["status"] = "error"
            results["errors"].append(error_msg)
            registry.update_status(file_hash, status="error", error_message=error_msg)

        # Update cache
        self.processed_pdfs[file_hash] = {
            "pdf_path": str(pdf_file),
            "processed_at": results["processed_at"],
            "text_chunks_count": len(results["text_chunks"]),
            "images_count": len(results["images_extracted"]),
            "status": results["status"]
        }
        self._save_processed_cache()

        return results

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def _extract_pdf_content(
        self,
        pdf_file: Path,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Extract text and images from PDF using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return {
                "errors": ["PyMuPDF not installed. Install with: pip install PyMuPDF"],
                "text_chunks": [],
                "images_extracted": []
            }

        text_chunks = []
        images_extracted = []
        errors = []

        # PDF metadata
        base_metadata = metadata or {}
        base_metadata.update({
            "source": pdf_file.name,
            "processed_at": datetime.now().isoformat()
        })

        # Enrich metadata if enabled
        if self.metadata_config.get("enrich", True):
            base_metadata = self._enrich_metadata(base_metadata, pdf_file.name)

        # Open PDF
        doc = fitz.open(pdf_file)

        # Extraction settings
        extract_images = self.pdf_config.get("extract_images", True)
        min_image_size = tuple(self.pdf_config.get("min_image_size", [100, 100]))
        max_images = self.pdf_config.get("max_images_per_pdf", 50)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_number = page_num + 1

            # Extract text
            text = page.get_text()
            if text.strip():
                # Create LlamaIndex document
                chunk_metadata = base_metadata.copy()
                chunk_metadata["page"] = page_number
                chunk_metadata["chunk_type"] = "text"

                text_chunks.append({
                    "content": text,
                    "metadata": chunk_metadata
                })

            # Extract images
            if extract_images and len(images_extracted) < max_images:
                try:
                    image_list = page.get_images(full=True)

                    for img_index, img in enumerate(image_list):
                        if len(images_extracted) >= max_images:
                            break

                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)

                        # Skip small images
                        if pix.width < min_image_size[0] or pix.height < min_image_size[1]:
                            continue

                        # Convert to RGB if necessary
                        if pix.n > 4:
                            pix = fitz.Pixmap(fitz.csRGB, pix)

                        # Save image
                        image_filename = f"{pdf_file.stem}_p{page_number}_img{img_index}.png"
                        image_path = self.extracted_images_dir / image_filename
                        pix.save(str(image_path))

                        img_metadata = base_metadata.copy()
                        img_metadata.update({
                            "page": page_number,
                            "image_index": img_index,
                            "width": pix.width,
                            "height": pix.height,
                            "xref": xref,
                            "extracted_from": str(pdf_file)
                        })

                        images_extracted.append({
                            "path": str(image_path),
                            "metadata": img_metadata
                        })

                except Exception as e:
                    errors.append(f"Error extracting images from page {page_number}: {str(e)}")

        total_pages = len(doc)
        doc.close()

        return {
            "text_chunks": text_chunks,
            "images_extracted": images_extracted,
            "errors": errors,
            "total_pages": total_pages,
            "text_chunks_count": len(text_chunks),
            "images_count": len(images_extracted)
        }

    def _enrich_metadata(self, metadata: Dict, filename: str) -> Dict:
        """Enrich metadata with additional fields and infer from filename"""
        fields = self.metadata_config.get("fields", [])
        enriched = metadata.copy()

        # Infer cultural context from filename
        cultural_context = self._infer_cultural_context(filename)
        if cultural_context:
            enriched["cultural_context"] = [cultural_context]

        for field in fields:
            if field not in enriched:
                if field == "type":
                    enriched[field] = "academic_paper"
                elif field == "date":
                    enriched[field] = datetime.now().strftime("%Y-%m-%d")
                elif field == "language":
                    enriched[field] = "en"
                elif field == "perspective":
                    enriched[field] = "western_academic"
                elif field == "institution":
                    enriched[field] = "unknown"

        # Infer from filename patterns
        filename_lower = filename.lower()
        if "indigenous" in filename_lower:
            enriched["perspective"] = "indigenous"
        elif "local" in filename_lower:
            enriched["perspective"] = "local"
        elif "colonial" in filename_lower:
            enriched["perspective"] = "colonial"

        if "archive" in filename_lower:
            enriched["type"] = "archive"
        elif "oral" in filename_lower or "interview" in filename_lower:
            enriched["type"] = "oral_history"

        return enriched

    def _infer_cultural_context(self, filename: str) -> Optional[str]:
        """Infer cultural context from filename"""
        filename_lower = filename.lower()

        contexts = {
            "olmec": "Olmec",
            "maya": "Maya",
            "aztec": "Aztec",
            "mixtec": "Mixtec",
            "zapotec": "Zapotec",
            "teotihuacan": "Teotihuacan",
            "toltec": "Toltec",
            "mexica": "Mexica",
            "tikal": "Maya",
            "copan": "Maya",
            "palenque": "Maya",
            "chichen": "Maya",
            "monte_alban": "Zapotec",
            "mitla": "Mixtec"
        }

        for keyword, context in contexts.items():
            if keyword in filename_lower:
                return context

        return "Mesoamerican"

    async def _index_text_chunks(self, chunks: List[Dict], source_name: str, doc_id: str = None):
        """Index text chunks using LlamaIndex + Qdrant"""
        registry = self._get_document_registry() if doc_id else None
        await self._index_text_chunks_with_progress(chunks, source_name, doc_id, registry)

    async def _process_images(self, images: List[Dict]):
        """Process extracted images with CLIP embeddings"""
        print(f"Processing {len(images)} images with CLIP...")

        for i, img_data in enumerate(images):
            try:
                await self.vision_agent.add_image(
                    img_data["path"],
                    img_data["metadata"]
                )
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(images)} images...")
            except Exception as e:
                print(f"Error processing image {img_data['path']}: {e}")

        print(f"✓ Processed {len(images)} images")

    async def process_directory(
        self,
        directory: str,
        pattern: str = "*.pdf",
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Process all PDFs in a directory"""
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"status": "error", "message": f"Directory not found: {directory}"}

        pdf_files = list(dir_path.glob(pattern))

        results = {
            "directory": str(dir_path),
            "pdfs_found": len(pdf_files),
            "processed": [],
            "failed": [],
            "cached": []
        }

        for pdf_file in pdf_files:
            print(f"\nProcessing {pdf_file.name}...")

            # Register document if not already in registry
            file_hash = self._calculate_file_hash(pdf_file)
            registry = self._get_document_registry()
            if not registry.get_document(file_hash):
                file_type = self._get_file_type(pdf_file.suffix)
                registry.register_document(
                    doc_id=file_hash,
                    filename=pdf_file.name,
                    filepath=str(pdf_file),
                    file_size=pdf_file.stat().st_size,
                    file_type=file_type,
                    metadata=metadata
                )

            result = await self.process_pdf(str(pdf_file), metadata)

            if result["status"] == "success":
                results["processed"].append({
                    "path": str(pdf_file),
                    "chunks": result.get("text_chunks_count", 0),
                    "images": result.get("images_count", 0)
                })
            elif result["status"] == "cached":
                results["cached"].append(str(pdf_file))
                # Update registry to indexed if cached
                registry.update_status(file_hash, status="indexed")
            else:
                results["failed"].append({
                    "path": str(pdf_file),
                    "error": result.get("errors", ["Unknown error"])
                })

        print(f"\n{'='*60}")
        print(f"Directory processing complete!")
        print(f"  Processed: {len(results['processed'])}")
        print(f"  Cached: {len(results['cached'])}")
        print(f"  Failed: {len(results['failed'])}")
        print(f"{'='*60}")

        return results

    def get_processing_status(self, pdf_path: str) -> Optional[Dict]:
        """Check if a PDF has been processed"""
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return None

        file_hash = self._calculate_file_hash(pdf_file)
        return self.processed_pdfs.get(file_hash)

    def _get_document_registry(self):
        """Get or create the document registry instance"""
        if self._document_registry is None:
            from utils.document_registry import get_registry
            self._document_registry = get_registry()
        return self._document_registry

    def _get_file_type(self, extension: str) -> str:
        """Map file extension to type category"""
        ext_lower = extension.lower()
        if ext_lower == '.pdf':
            return 'pdf'
        elif ext_lower in ['.png', '.jpg', '.jpeg', '.tiff', '.gif', '.bmp', '.webp']:
            return 'image'
        elif ext_lower in ['.txt', '.md', '.rst']:
            return 'text'
        elif ext_lower in ['.docx', '.doc', '.odt']:
            return 'document'
        return 'unknown'

    async def _index_text_chunks_with_progress(
        self,
        chunks: List[Dict],
        source_name: str,
        doc_id: str,
        registry
    ):
        """Index text chunks with progress updates to registry"""
        try:
            from llama_index.core import Document

            # Convert chunks to LlamaIndex Documents
            documents = []
            for chunk in chunks:
                doc = Document(
                    text=chunk["content"],
                    metadata=chunk["metadata"]
                )
                documents.append(doc)

            # Index through retrieval agent
            self.retrieval_agent.index_documents(documents)

            # Update progress
            registry.update_status(
                doc_id,
                status="indexing",
                chunks_indexed=len(documents)
            )

            print(f"✓ Indexed {len(documents)} text chunks from {source_name}")

        except Exception as e:
            print(f"Warning: Could not index text chunks: {e}")
            # Fallback: save to local JSON
            output_file = self.data_dir / "text_chunks" / f"{source_name}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(chunks, f, indent=2)


# Convenience function for CLI usage
async def ingest_pdf(pdf_path: str, **kwargs) -> Dict[str, Any]:
    """Ingest a single PDF file"""
    pipeline = MultimodalIngestPipeline()
    return await pipeline.process_pdf(pdf_path, **kwargs)


async def ingest_directory(directory: str, **kwargs) -> Dict[str, Any]:
    """Ingest all PDFs in a directory"""
    pipeline = MultimodalIngestPipeline()
    return await pipeline.process_directory(directory, **kwargs)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python multimodal_ingest.py <pdf_file_or_directory>")
        sys.exit(1)

    path = sys.argv[1]

    if Path(path).is_file():
        result = asyncio.run(ingest_pdf(path))
    else:
        result = asyncio.run(ingest_directory(path))

    print(json.dumps(result, indent=2))
