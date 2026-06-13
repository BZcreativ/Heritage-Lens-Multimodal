"""
Test script for video indexing + timestamped search.
Creates a synthetic video with a known spoken phrase, indexes it,
and verifies that a query returns the correct timestamp + metadata.

Usage:
    cd heritage-lens-multimodal
    source venv/bin/activate
    python tests/test_video_ingest.py

Requirements:
    - faster-whisper (installed)
    - ffmpeg (system binary)
    - Qdrant running at localhost:6333
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests._util import setup_collection, teardown_collection  # forces HL_TEXT_COLLECTION before agent imports
from agent.env_loader import load_env

load_env()

from qdrant_client import QdrantClient
from agent.video_ingest import index_video_audio
from agent.retriever import retrieve_chunks

# ── Constants ────────────────────────────────────────────────────────────────
TEST_PHRASE = "The obsidian blade was used in ritual ceremonies at La Venta"
VIDEO_DURATION = 8  # seconds
TEST_VOICE = "en"     # or "it" for Italian; espeak-ng voice code


def create_synthetic_video(output_path: str, text: str, duration: int = 8) -> str:
    """
    Create a synthetic MP4 with spoken text using espeak-ng + ffmpeg.
    Requires espeak-ng and ffmpeg installed on the system.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "audio.wav")
        # Generate speech with espeak-ng (lightweight, no cloud dependency)
        cmd = [
            "espeak-ng",
            "-v", "en",
            "-s", "120",        # speed
            "-w", wav_path,
            text,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except FileNotFoundError:
            print("ERROR: espeak-ng not found. Install with: sudo apt-get install espeak-ng")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: espeak-ng failed: {e.stderr.decode()}")
            sys.exit(1)

        # Create a blank video (blue frame) with the audio
        # Use lavfi color source for reliable solid-color video
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=blue:s=320x240:d={duration}",
            "-i", wav_path,
            "-shortest",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            output_path,
        ], check=True, capture_output=True)
    return output_path


def test_video_audio_pipeline():
    """
    End-to-end test:
    1. Create synthetic video with TEST_PHRASE
    2. Index audio transcript into Qdrant
    3. Query Qdrant for a keyword from the phrase
    4. Assert the returned chunk has correct timestamp + metadata
    """
    print("=" * 60)
    print("VIDEO INGESTION + TIMESTAMPED SEARCH TEST")
    print("=" * 60)

    client = QdrantClient(url="http://localhost:6333")
    setup_collection(client)

    # 1. Create synthetic video
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        print(f"[1/4] Creating synthetic video at {video_path}...")
        create_synthetic_video(video_path, TEST_PHRASE, duration=VIDEO_DURATION)
        print(f"      Video created: {os.path.getsize(video_path)} bytes")

        # 2. Index audio
        print(f"[2/4] Indexing audio transcript...")
        n = index_video_audio(video_path, client, video_url=f"file://{video_path}")
        print(f"      Indexed {n} audio transcript chunks")
        assert n > 0, "No audio chunks indexed — transcription failed or no speech detected"

    # 3. Query for a keyword
    query = "obsidian blade ritual La Venta"
    print(f"[3/4] Querying: '{query}'")
    chunks = retrieve_chunks(query, top_k=5)
    print(f"      Retrieved {len(chunks)} chunks")
    assert len(chunks) > 0, "No chunks retrieved — check embeddings or query"

    # 4. Verify metadata
    print(f"[4/4] Verifying chunk metadata...")
    found_video_chunk = False
    for i, ch in enumerate(chunks):
        meta = ch.get("metadata", {})
        print(f"      Chunk {i}: modality={meta.get('modality')}, "
              f"start={meta.get('start')}, end={meta.get('end')}, "
              f"source={meta.get('source_name')}")

        if meta.get("modality") == "audio_transcript":
            found_video_chunk = True
            assert "start" in meta, "Missing 'start' timestamp"
            assert "end" in meta, "Missing 'end' timestamp"
            assert meta.get("video_id") is not None, "Missing 'video_id'"
            assert meta.get("video_url") is not None, "Missing 'video_url'"
            assert meta.get("source_type") == "video", "source_type should be 'video'"
            # The chunk should be somewhere within the video duration
            assert 0 <= meta["start"] <= VIDEO_DURATION, f"start {meta['start']} out of range"
            assert 0 <= meta["end"] <= VIDEO_DURATION, f"end {meta['end']} out of range"
            # The text should contain at least part of the spoken phrase
            chunk_text = ch.get("text", "").lower()
            assert "obsidian" in chunk_text or "blade" in chunk_text or "ritual" in chunk_text or "la venta" in chunk_text, \
                f"Chunk text doesn't match expected content: {chunk_text[:80]}"

    assert found_video_chunk, "No audio_transcript chunk found in retrieval results"

    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nVideo indexing works end-to-end:")
    print(f"  - {n} audio transcript chunks indexed")
    print(f"  - Retrieval returned {len(chunks)} chunks with correct timestamps")
    print(f"  - Metadata fields: modality, video_id, video_url, start, end all present")


if __name__ == "__main__":
    try:
        test_video_audio_pipeline()
    finally:
        teardown_collection(QdrantClient(url="http://localhost:6333"))
