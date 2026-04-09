"""
Document Registry
Tracks document indexing status and metadata for the Archive Panel
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

PROJECT_ROOT = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")


@dataclass
class DocumentRecord:
    """Represents a document in the registry"""
    id: str
    filename: str
    filepath: str
    file_size: int
    file_type: str
    status: str  # 'queued', 'indexing', 'indexed', 'error'
    chunks_indexed: int = 0
    chunks_total: int = 0
    images_extracted: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None
    added_at: Optional[str] = None
    updated_at: Optional[str] = None


class DocumentRegistry:
    """
    SQLite-based document registry for tracking indexing status.
    Provides real-time status updates for the Archive Panel.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else PROJECT_ROOT / "data" / "document_registry.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT DEFAULT 'unknown',
                    status TEXT DEFAULT 'queued',
                    chunks_indexed INTEGER DEFAULT 0,
                    chunks_total INTEGER DEFAULT 0,
                    images_extracted INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for faster queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON documents(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename)")
            conn.commit()

    def register_document(
        self,
        doc_id: str,
        filename: str,
        filepath: str,
        file_size: int = 0,
        file_type: str = "unknown",
        metadata: Optional[Dict] = None
    ) -> DocumentRecord:
        """
        Register a new document in the registry.
        Called when a document is uploaded.
        """
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO documents
                (id, filename, filepath, file_size, file_type, status, metadata, added_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?)
            """, (doc_id, filename, filepath, file_size, file_type,
                  json.dumps(metadata) if metadata else None, now, now))
            conn.commit()

        return self.get_document(doc_id)

    def update_status(
        self,
        doc_id: str,
        status: str,
        chunks_indexed: Optional[int] = None,
        chunks_total: Optional[int] = None,
        images_extracted: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[DocumentRecord]:
        """
        Update document indexing status.
        Called during the ingestion pipeline to report progress.
        """
        now = datetime.now().isoformat()

        updates = ["status = ?", "updated_at = ?"]
        params = [status, now]

        if chunks_indexed is not None:
            updates.append("chunks_indexed = ?")
            params.append(chunks_indexed)
        if chunks_total is not None:
            updates.append("chunks_total = ?")
            params.append(chunks_total)
        if images_extracted is not None:
            updates.append("images_extracted = ?")
            params.append(images_extracted)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        params.append(doc_id)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE documents SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

        return self.get_document(doc_id)

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        """Get a single document by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()

            if row:
                return self._row_to_record(row)
            return None

    def get_document_by_filename(self, filename: str) -> Optional[DocumentRecord]:
        """Get a document by filename"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE filename = ? ORDER BY added_at DESC LIMIT 1",
                (filename,)
            ).fetchone()

            if row:
                return self._row_to_record(row)
            return None

    def list_documents(
        self,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentRecord]:
        """
        List documents with optional filtering.
        Used by the Archive Panel to display the document list.
        """
        query = "SELECT * FROM documents"
        params = []
        conditions = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY added_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(row) for row in rows]

    def search_documents(self, query: str, limit: int = 20) -> List[DocumentRecord]:
        """Search documents by filename"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE filename LIKE ? ORDER BY added_at DESC LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()
            return [self._row_to_record(row) for row in rows]

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document from the registry"""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get document registry statistics"""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            indexed = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE status = 'indexed'"
            ).fetchone()[0]
            indexing = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE status = 'indexing'"
            ).fetchone()[0]
            queued = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE status = 'queued'"
            ).fetchone()[0]
            errors = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE status = 'error'"
            ).fetchone()[0]

            return {
                "total": total,
                "indexed": indexed,
                "indexing": indexing,
                "queued": queued,
                "errors": errors
            }

    def _row_to_record(self, row: sqlite3.Row) -> DocumentRecord:
        """Convert database row to DocumentRecord"""
        return DocumentRecord(
            id=row["id"],
            filename=row["filename"],
            filepath=row["filepath"],
            file_size=row["file_size"],
            file_type=row["file_type"],
            status=row["status"],
            chunks_indexed=row["chunks_indexed"],
            chunks_total=row["chunks_total"],
            images_extracted=row["images_extracted"],
            error_message=row["error_message"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            added_at=row["added_at"],
            updated_at=row["updated_at"]
        )

    def to_dict_list(self, records: List[DocumentRecord]) -> List[Dict]:
        """Convert records to list of dicts for JSON serialization"""
        return [asdict(r) for r in records]


# Global registry instance (lazy-loaded)
_registry: Optional[DocumentRegistry] = None


def get_registry() -> DocumentRegistry:
    """Get or create the global document registry instance"""
    global _registry
    if _registry is None:
        _registry = DocumentRegistry()
    return _registry
