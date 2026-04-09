"""
Persistent conversation history storage using SQLite
Enables session persistence across restarts
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class ConversationStore:
    """
    SQLite-backed conversation storage with JSON serialization
    Provides persistent session history for the Heritage Lens system
    """

    def __init__(self, db_path: str = None):
        """
        Initialize conversation store

        Args:
            db_path: Path to SQLite database. If None, uses data/conversations.db
        """
        if db_path is None:
            # Detect project root - works in both Docker and local environments
            project_root = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")
            db_path = project_root / "data" / "conversations.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_db()

    def _init_db(self):
        """Create database tables if not exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT  -- JSON blob for session-level metadata
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,  -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON blob for message-level metadata (layers, sources, etc.)
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, timestamp)
            """)

            conn.commit()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict = None
    ) -> int:
        """
        Add a message to a session

        Args:
            session_id: Unique session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (e.g., layers, sources, processing info)

        Returns:
            Message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            # Ensure session exists
            conn.execute(
                """INSERT OR IGNORE INTO sessions (session_id) VALUES (?)""",
                (session_id,)
            )

            # Update session timestamp
            conn.execute(
                """UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?""",
                (session_id,)
            )

            # Insert message
            cursor = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, json.dumps(metadata) if metadata else None)
            )

            conn.commit()
            return cursor.lastrowid

    def get_history(
        self,
        session_id: str,
        limit: int = 20,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (default 20)
            include_metadata: Whether to include metadata in results

        Returns:
            List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT role, content, timestamp{}
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """.format(", metadata" if include_metadata else "")

            rows = conn.execute(query, (session_id, limit)).fetchall()

            messages = []
            for row in rows:
                msg = {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                }
                if include_metadata and row["metadata"]:
                    msg["metadata"] = json.loads(row["metadata"])
                messages.append(msg)

            return messages

    def list_sessions(
        self,
        limit: int = 50,
        include_message_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all sessions

        Args:
            limit: Maximum number of sessions to return
            include_message_count: Whether to include message count per session

        Returns:
            List of session dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if include_message_count:
                rows = conn.execute(
                    """
                    SELECT
                        s.session_id,
                        s.created_at,
                        s.updated_at,
                        COUNT(m.id) as message_count
                    FROM sessions s
                    LEFT JOIN messages m ON s.session_id = m.session_id
                    GROUP BY s.session_id
                    ORDER BY s.updated_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT session_id, created_at, updated_at
                    FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                ).fetchall()

            return [dict(row) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages

        Args:
            session_id: Session to delete

        Returns:
            True if session was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search sessions by content

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            List of matching sessions with preview
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """
                SELECT DISTINCT
                    s.session_id,
                    s.created_at,
                    s.updated_at,
                    (SELECT content FROM messages
                     WHERE session_id = s.session_id AND role = 'user'
                     ORDER BY timestamp DESC LIMIT 1) as last_query
                FROM sessions s
                JOIN messages m ON s.session_id = m.session_id
                WHERE m.content LIKE ?
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (f"%{query}%", limit)
            ).fetchall()

            return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            session_count = conn.execute(
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0]

            message_count = conn.execute(
                "SELECT COUNT(*) FROM messages"
            ).fetchone()[0]

            return {
                "sessions": session_count,
                "messages": message_count,
                "db_path": str(self.db_path)
            }

    def export_session(self, session_id: str, format: str = "json") -> str:
        """
        Export a session to JSON or markdown

        Args:
            session_id: Session to export
            format: 'json' or 'markdown'

        Returns:
            Exported content as string
        """
        messages = self.get_history(session_id, limit=1000, include_metadata=True)

        if not messages:
            return ""

        if format == "json":
            return json.dumps({
                "session_id": session_id,
                "exported_at": datetime.now().isoformat(),
                "messages": messages
            }, indent=2)

        elif format == "markdown":
            lines = [f"# Conversation: {session_id}\n"]
            lines.append(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

            for msg in messages:
                timestamp = msg["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = timestamp.split(".")[0]  # Remove microseconds

                if msg["role"] == "user":
                    lines.append(f"\n## User ({timestamp})\n")
                else:
                    lines.append(f"\n## Assistant ({timestamp})\n")

                lines.append(msg["content"])
                lines.append("")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")


# Singleton instance for application-wide use
_store_instance: Optional[ConversationStore] = None


def get_conversation_store(db_path: str = None) -> ConversationStore:
    """Get or create singleton conversation store instance"""
    global _store_instance
    if _store_instance is None:
        _store_instance = ConversationStore(db_path)
    return _store_instance
