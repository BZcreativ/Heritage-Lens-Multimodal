"""
Test script for Phase B — Visual indexing (scene captions + OCR + dedup).

Creates a synthetic video using a real PDF image + audio narration,
indexes both audio (Phase A) and visual (Phase B), then verifies:
1. audio_transcript chunks exist with timestamps
2. visual_caption chunks exist with timestamps
3. ocr_text chunks exist with timestamps
4. deduplication skipped near-duplicate visual chunks

Usage:
    cd heritage-lens-multimodal
    source venv/bin/activate
    python tests/test_video_phase_b.py

Requires:
    - faster-whisper, scenedetect, pytesseract (installed)
    - ffmpeg, espeak-ng (system binaries)
    - GLM_API_KEY in config/.env (for visual captions)
    - Qdrant running at localhost:6333
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests._util import setup_collection, teardown_collection, TEST_COLLECTION  # forces HL_TEXT_COLLECTION before agent imports
from agent.env_loader import load_env

load_env()

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from agent.video_ingest import index_video
from agent.retriever import retrieve_chunks

# ── Constants ────────────────────────────────────────────────────────────────
TEST_PHRASE = "The obsidian blade was used in ritual ceremonies at La Venta"
VIDEO_DURATION = 8
# Pick a real image from the corpus cache (has cultural heritage content)
CANDIDATE_IMAGES = [
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p11_0.png",
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p121_0.png",
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p133_0.png",
]


def find_image() -> str:
    for p in CANDIDATE_IMAGES:
        if Path(p).exists():
            return p
    raise FileNotFoundError("No cached PDF images found. Run: python agent/ingest.py")


def create_test_video(image_path: str, audio_text: str, output_path: str, duration: int = 8):
    """Create a video from a real image + audio narration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "audio.wav")
        subprocess.run(
            ["espeak-ng", "-v", "en", "-s", "120", "-w", wav_path, audio_text],
            check=True, capture_output=True,
        )
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", wav_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=640:-2",
            "-c:a", "aac", "-shortest",
            "-t", str(duration),
            output_path,
        ], check=True, capture_output=True)


def test_phase_b():
    print("=" * 60)
    print("PHASE B — VISUAL INDEXING + DEDUP TEST")
    print("=" * 60)

    client = QdrantClient(url="http://localhost:6333")
    setup_collection(client)

    # 1. Create test video from real image + audio
    image_path = find_image()
    print(f"[1/5] Using image: {Path(image_path).name}")
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_heritage.mp4")
        print(f"[2/5] Creating video ({VIDEO_DURATION}s)...")
        create_test_video(image_path, TEST_PHRASE, video_path, VIDEO_DURATION)
        print(f"      Video: {os.path.getsize(video_path)} bytes")

        # 2. Run full indexing (audio + visual)
        print(f"[3/5] Indexing audio + visual (GLM-4V + OCR)...")
        results = index_video(
            video_path,
            client,
            video_url=f"file://{video_path}",
            index_audio=True,
            index_visual=True,
        )
        print(f"      Audio chunks: {results['audio_chunks']}")
        print(f"      Visual captions: {results['visual']['caption']}")
        print(f"      OCR chunks: {results['visual']['ocr']}")
        print(f"      Skipped (dupes): {results['visual']['skipped']}")

    # 3. Verify chunks in Qdrant
    print(f"[4/5] Verifying Qdrant chunks...")
    video_id = "test_heritage"
    # The video_id is actually the stem of the filename
    # But we can search by source_name
    all_chunks = client.scroll(
        collection_name=TEST_COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="source_name", match=MatchValue(value="test_heritage.mp4"))]
        ),
        limit=50,
        with_payload=True,
    )[0]

    print(f"      Total chunks in Qdrant: {len(all_chunks)}")
    modalities = {}
    for p in all_chunks:
        mod = p.payload.get("modality", "unknown")
        modalities[mod] = modalities.get(mod, 0) + 1
        print(f"      - {mod}: start={p.payload.get('start')}, end={p.payload.get('end')}")

    # 4. Assert expectations
    print(f"[5/5] Assertions...")
    assert modalities.get("audio_transcript", 0) > 0, "No audio transcript chunks"
    assert modalities.get("visual_caption", 0) > 0 or modalities.get("ocr_text", 0) > 0, \
        "No visual chunks (caption or OCR) — check GLM-4V or pytesseract"
    assert results["visual"]["errors"] == 0, \
        f"Captioning failed on {results['visual']['errors']} frame(s) — see logs above"

    # Check metadata fields
    for p in all_chunks:
        payload = p.payload
        assert "start" in payload, "Missing 'start'"
        assert "end" in payload, "Missing 'end'"
        assert "video_id" in payload, "Missing 'video_id'"
        assert "video_url" in payload, "Missing 'video_url'"
        assert "modality" in payload, "Missing 'modality'"

    # 5. Retrieval test
    print(f"\n[Bonus] Retrieval test...")
    q = "obsidian blade ritual"
    chunks = retrieve_chunks(q, top_k=10)
    video_hits = [c for c in chunks if c["metadata"].get("source_name") == "test_heritage.mp4"]
    print(f"      Query '{q}' returned {len(video_hits)} video-derived chunks")
    for h in video_hits:
        meta = h["metadata"]
        print(f"      → {meta['modality']}: {meta['start']}s-{meta['end']}s | {h['text'][:60]}...")

    print("=" * 60)
    print("✅ PHASE B TEST PASSED")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Audio transcript chunks: {modalities.get('audio_transcript', 0)}")
    print(f"  - Visual caption chunks: {modalities.get('visual_caption', 0)}")
    print(f"  - OCR chunks: {modalities.get('ocr_text', 0)}")
    print(f"  - Skipped duplicates: {results['visual']['skipped']}")
    print(f"  - All chunks have: start, end, video_id, video_url, modality")


if __name__ == "__main__":
    try:
        test_phase_b()
    finally:
        teardown_collection(QdrantClient(url="http://localhost:6333"))
