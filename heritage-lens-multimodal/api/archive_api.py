"""
Archive API Endpoints
REST API for document registry operations
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

PROJECT_ROOT = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")


class ArchiveAPI:
    """
    API handler for Archive Panel operations.
    Provides endpoints for listing, searching, and scoping documents.
    """

    def __init__(self):
        from utils.document_registry import get_registry
        self.registry = get_registry()

    def get_documents(
        self,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get list of documents with optional filtering.

        Args:
            status: Filter by status ('queued', 'indexing', 'indexed', 'error')
            file_type: Filter by file type ('pdf', 'image', 'txt', etc.)
            search: Search query for filename
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dict with documents list and total count
        """
        if search:
            documents = self.registry.search_documents(search, limit=limit)
        else:
            documents = self.registry.list_documents(
                status=status,
                file_type=file_type,
                limit=limit,
                offset=offset
            )

        stats = self.registry.get_stats()

        return {
            "documents": self.registry.to_dict_list(documents),
            "total": stats["total"],
            "stats": stats,
            "limit": limit,
            "offset": offset
        }

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        doc = self.registry.get_document(doc_id)
        if doc:
            return {
                "id": doc.id,
                "filename": doc.filename,
                "filepath": doc.filepath,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "status": doc.status,
                "chunks_indexed": doc.chunks_indexed,
                "chunks_total": doc.chunks_total,
                "images_extracted": doc.images_extracted,
                "error_message": doc.error_message,
                "metadata": doc.metadata,
                "added_at": doc.added_at,
                "updated_at": doc.updated_at,
                "progress_percent": self._calculate_progress(doc)
            }
        return None

    def _calculate_progress(self, doc) -> int:
        """Calculate indexing progress percentage"""
        if doc.status == "indexed":
            return 100
        if doc.status in ["queued", "error"]:
            return 0
        if doc.chunks_total > 0:
            return int((doc.chunks_indexed / doc.chunks_total) * 100)
        return 0

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document from the registry"""
        success = self.registry.delete_document(doc_id)
        return {
            "success": success,
            "message": "Document deleted" if success else "Document not found"
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get document registry statistics"""
        return self.registry.get_stats()

    def sync_with_corpus(self) -> Dict[str, Any]:
        """
        Sync registry with actual corpus files.
        Adds any new files found in the corpus directory.
        """
        import hashlib

        corpus_dir = PROJECT_ROOT / "data" / "corpus"
        if not corpus_dir.exists():
            return {"success": False, "message": "Corpus directory not found"}

        added_count = 0
        existing_files = {d.filename for d in self.registry.list_documents(limit=1000)}

        for file_path in corpus_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.txt']:
                if file_path.name not in existing_files:
                    # Generate ID from file hash
                    file_hash = self._calculate_file_hash(file_path)

                    # Determine file type
                    file_type = self._get_file_type(file_path.suffix)

                    self.registry.register_document(
                        doc_id=file_hash,
                        filename=file_path.name,
                        filepath=str(file_path),
                        file_size=file_path.stat().st_size,
                        file_type=file_type
                    )
                    added_count += 1

        return {
            "success": True,
            "message": f"Synced {added_count} new documents",
            "added_count": added_count
        }

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for ID"""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_file_type(self, extension: str) -> str:
        """Map file extension to type category"""
        ext_lower = extension.lower()
        if ext_lower == '.pdf':
            return 'pdf'
        elif ext_lower in ['.png', '.jpg', '.jpeg', '.tiff', '.gif', '.bmp']:
            return 'image'
        elif ext_lower in ['.txt', '.md', '.rst']:
            return 'text'
        elif ext_lower in ['.docx', '.doc', '.odt']:
            return 'document'
        return 'unknown'


# FastAPI router (optional - if using FastAPI)
try:
    from fastapi import APIRouter, HTTPException, Query
    from typing import Optional

    router = APIRouter(prefix="/api/archive", tags=["archive"])

    @router.get("/documents")
    async def api_get_documents(
        status: Optional[str] = Query(None, description="Filter by status"),
        file_type: Optional[str] = Query(None, description="Filter by file type"),
        search: Optional[str] = Query(None, description="Search filename"),
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0)
    ):
        """Get list of documents in the archive"""
        api = ArchiveAPI()
        return api.get_documents(status, file_type, search, limit, offset)

    @router.get("/documents/{doc_id}")
    async def api_get_document(doc_id: str):
        """Get a single document by ID"""
        api = ArchiveAPI()
        doc = api.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    @router.delete("/documents/{doc_id}")
    async def api_delete_document(doc_id: str):
        """Delete a document from the registry"""
        api = ArchiveAPI()
        result = api.delete_document(doc_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result

    @router.get("/stats")
    async def api_get_stats():
        """Get document registry statistics"""
        api = ArchiveAPI()
        return api.get_stats()

    @router.post("/sync")
    async def api_sync_corpus():
        """Sync registry with corpus directory"""
        api = ArchiveAPI()
        return api.sync_with_corpus()

except ImportError:
    # FastAPI not installed, skip router
    router = None


# Singleton instance
def get_archive_api() -> ArchiveAPI:
    """Get ArchiveAPI instance"""
    return ArchiveAPI()
