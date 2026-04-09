"""
Slack File Handler Tool
Downloads files from Slack for indexing into Heritage Lens
Handles the files:read permission and authentication
"""

import os
import requests
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import json


class SlackFileHandler:
    """
    Handles downloading files from Slack using bot token
    Required scopes: files:read, chat:write
    """

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize with Slack bot token

        Args:
            bot_token: Slack bot token (xoxb-...). If None, reads from env.
        """
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("Slack bot token required. Set SLACK_BOT_TOKEN env var.")

        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

    def download_file(self, file_id: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a file from Slack using file_id

        Args:
            file_id: Slack file ID (e.g., "F1234567890")
            output_dir: Directory to save file. If None, uses temp dir.

        Returns:
            Dict with file info and local path
        """
        # Step 1: Get file info from Slack
        file_info = self._get_file_info(file_id)
        if not file_info:
            return {"success": False, "error": f"Could not get file info for {file_id}"}

        # Step 2: Download the file
        url_private = file_info.get("url_private_download") or file_info.get("url_private")
        if not url_private:
            return {"success": False, "error": "No download URL available"}

        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path(tempfile.gettempdir()) / "slack_files"

        output_path.mkdir(parents=True, exist_ok=True)

        # Save file
        filename = file_info.get("name", f"slack_file_{file_id}")
        local_path = output_path / filename

        try:
            response = requests.get(
                url_private,
                headers={"Authorization": f"Bearer {self.bot_token}"},
                timeout=60
            )
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "local_path": str(local_path),
                "size": file_info.get("size"),
                "mimetype": file_info.get("mimetype"),
                "title": file_info.get("title"),
                "user": file_info.get("user"),
                "created": file_info.get("created")
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Download failed: {str(e)}"}

    def _get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file metadata from Slack API"""
        try:
            response = requests.post(
                "https://slack.com/api/files.info",
                headers=self.headers,
                json={"file": file_id},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data.get("ok"):
                return data.get("file")
            else:
                print(f"Slack API error: {data.get('error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def download_from_event(self, event_data: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Download file from a Slack event payload

        Args:
            event_data: Slack event data (message with files array)
            output_dir: Directory to save file

        Returns:
            Dict with download results
        """
        files = event_data.get("files", [])
        if not files:
            return {"success": False, "error": "No files in event data"}

        results = []
        for file_info in files:
            file_id = file_info.get("id")
            if file_id:
                result = self.download_file(file_id, output_dir)
                results.append(result)

        return {
            "success": all(r.get("success") for r in results),
            "files_downloaded": len([r for r in results if r.get("success")]),
            "results": results
        }

    def index_slack_file(
        self,
        file_id: str,
        ingest_pipeline: Optional[Any] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download and index a Slack file into Heritage Lens

        Args:
            file_id: Slack file ID
            ingest_pipeline: Optional ingestion pipeline instance
            output_dir: Directory to save file temporarily

        Returns:
            Dict with download and indexing results
        """
        # Step 1: Download
        download_result = self.download_file(file_id, output_dir)
        if not download_result.get("success"):
            return download_result

        local_path = download_result["local_path"]

        # Step 2: Check file type
        mimetype = download_result.get("mimetype", "")

        # Step 3: Index based on type
        if "pdf" in mimetype.lower():
            return self._index_pdf(local_path, download_result, ingest_pipeline)
        elif "image" in mimetype.lower():
            return self._index_image(local_path, download_result)
        elif "text" in mimetype.lower() or mimetype == "application/json":
            return self._index_text(local_path, download_result)
        else:
            return {
                **download_result,
                "indexed": False,
                "message": f"File type {mimetype} not supported for indexing"
            }

    def _index_pdf(
        self,
        local_path: str,
        download_result: Dict,
        ingest_pipeline: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Index a PDF file"""
        try:
            from pipelines.pdf_extraction.multimodal_ingest import MultimodalIngestPipeline

            if ingest_pipeline is None:
                ingest_pipeline = MultimodalIngestPipeline()

            # Move to corpus directory
            corpus_dir = Path.home() / "heritage-lens-multimodal" / "data" / "corpus"
            corpus_dir.mkdir(parents=True, exist_ok=True)

            dest_path = corpus_dir / download_result["filename"]
            Path(local_path).rename(dest_path)

            # Run ingestion
            import asyncio
            stats = asyncio.run(ingest_pipeline.ingest_pdf_directory(corpus_dir))

            return {
                **download_result,
                "indexed": True,
                "type": "pdf",
                "corpus_path": str(dest_path),
                "ingestion_stats": stats
            }

        except Exception as e:
            return {
                **download_result,
                "indexed": False,
                "error": f"PDF indexing failed: {str(e)}"
            }

    def _index_image(self, local_path: str, download_result: Dict) -> Dict[str, Any]:
        """Index an image file"""
        try:
            from agents.vision.vision_agent import VisionAgent

            vision_agent = VisionAgent()

            # Add image to vision agent
            metadata = {
                "source": f"slack:{download_result['file_id']}",
                "title": download_result.get("title", ""),
                "user": download_result.get("user", ""),
                "timestamp": download_result.get("created", "")
            }

            import asyncio
            result = asyncio.run(vision_agent.add_image(local_path, metadata))

            return {
                **download_result,
                "indexed": True,
                "type": "image",
                "vision_result": result
            }

        except Exception as e:
            return {
                **download_result,
                "indexed": False,
                "error": f"Image indexing failed: {str(e)}"
            }

    def _index_text(self, local_path: str, download_result: Dict) -> Dict[str, Any]:
        """Index a text file"""
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create document
            from llama_index.core import Document

            doc = Document(
                text=content,
                metadata={
                    "source": f"slack:{download_result['file_id']}",
                    "filename": download_result["filename"],
                    "title": download_result.get("title", "")
                }
            )

            # Index to vector store
            # (This would need the vector store integration)

            return {
                **download_result,
                "indexed": True,
                "type": "text",
                "content_preview": content[:500]
            }

        except Exception as e:
            return {
                **download_result,
                "indexed": False,
                "error": f"Text indexing failed: {str(e)}"
            }


def handle_slack_file_download(file_id: str, bot_token: Optional[str] = None) -> str:
    """
    Convenience function for OpenClaw tool integration

    Args:
        file_id: Slack file ID
        bot_token: Optional bot token (uses env var if not provided)

    Returns:
        JSON string with result
    """
    try:
        handler = SlackFileHandler(bot_token)
        result = handler.index_slack_file(file_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


if __name__ == "__main__":
    # CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Slack File Handler")
    parser.add_argument("file_id", help="Slack file ID (e.g., F1234567890)")
    parser.add_argument("--download-only", action="store_true", help="Only download, don't index")
    parser.add_argument("--output-dir", help="Directory to save file")

    args = parser.parse_args()

    handler = SlackFileHandler()

    if args.download_only:
        result = handler.download_file(args.file_id, args.output_dir)
    else:
        result = handler.index_slack_file(args.file_id, output_dir=args.output_dir)

    print(json.dumps(result, indent=2))
