"""
Dry-run test for Phase B — no GLM-4V API calls.
Tests scene detection, frame extraction, OCR, and dedup mechanics
without making any external vision API calls.
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
from agent.video_ingest import index_video_audio
from PIL import Image
import pytesseract

CANDIDATE_IMAGES = [
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p11_0.png",
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p121_0.png",
    "data/cache/images/Formazione_della_Citta_in_Mesoamerica_p133_0.png",
]

def find_image() -> str:
    for p in CANDIDATE_IMAGES:
        if Path(p).exists():
            return p
    raise FileNotFoundError("No cached PDF images found.")

def test_phase_b_dry():
    print("=" * 60)
    print("PHASE B DRY-RUN (no GLM-4V API calls)")
    print("=" * 60)

    client = QdrantClient(url="http://localhost:6333")
    setup_collection(client)

    image_path = find_image()
    print(f"[1/6] Using image: {Path(image_path).name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "dry_test.mp4")
        frame_path = os.path.join(tmpdir, "frame.png")
        wav_path = os.path.join(tmpdir, "audio.wav")

        # 1. Create audio narration
        print(f"[2/6] Generating audio with espeak-ng...")
        subprocess.run([
            "espeak-ng", "-v", "en", "-s", "120", "-w", wav_path,
            "obsidian blade ritual ceremony",
        ], check=True, capture_output=True)

        # 2. Create video from image + audio
        print(f"[3/6] Creating 5s video from image + audio...")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", wav_path,
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=640:-2", "-c:a", "aac", "-t", "5",
            video_path,
        ], check=True, capture_output=True)
        print(f"      Video: {os.path.getsize(video_path)} bytes")

        # 3. Index audio (Phase A)
        print(f"[4/6] Indexing audio transcript (Phase A)...")
        n_audio = index_video_audio(video_path, client, video_url=f"file://{video_path}")
        print(f"      Audio chunks: {n_audio}")
        assert n_audio > 0, "No audio chunks"

        # 4. Scene detection
        print(f"[5/6] Scene detection (PySceneDetect)...")
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        video = open_video(video_path)
        sm = SceneManager()
        sm.add_detector(ContentDetector(threshold=20.0))  # lower threshold for static image
        sm.detect_scenes(video)
        scenes = sm.get_scene_list()
        print(f"      Scenes detected: {len(scenes)}")
        # Static image may return 0 or 1 scene — both are valid
        if not scenes:
            print("      (No scene changes detected — treating entire video as one scene)")
            scenes = [(video.base_timecode, video.duration)]

        # 5. Frame extraction + OCR
        print(f"[6/6] Frame extraction + OCR...")
        mid_sec = 2.0
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(mid_sec), "-i", video_path,
            "-vframes", "1", "-q:v", "2", frame_path,
        ], check=True, capture_output=True)
        img = Image.open(frame_path).convert("RGB")
        ocr_text = pytesseract.image_to_string(img).strip()
        print(f"      OCR result: {ocr_text[:120] if ocr_text else '(no text detected)'}...")

        # 6. Dedup check
        print(f"\n[Extra] Deduplication check...")
        from agent.video_ingest import _find_similar_chunk, _get_embedder
        embedder = _get_embedder()
        audio_chunks = client.scroll(
            collection_name=TEST_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="source_name", match=MatchValue(value="dry_test.mp4"))]
            ),
            limit=1,
            with_payload=True,
        )[0]
        assert len(audio_chunks) > 0, "No audio chunks found for dedup test"
        existing_vec = audio_chunks[0].vector
        is_duplicate = _find_similar_chunk(client, existing_vec, "dry_test", 0.0, 5.0)
        print(f"      Self-similar chunk flagged: {is_duplicate}")
        assert is_duplicate, "Dedup should find the existing chunk as similar"

        import random
        random_vec = [random.random() for _ in range(384)]
        is_not_dup = _find_similar_chunk(client, random_vec, "dry_test", 0.0, 5.0)
        print(f"      Random vector flagged: {is_not_dup}")
        assert not is_not_dup, "Random vector should not match anything"

        # 7. Embed a fake caption and verify it can be inserted
        print(f"\n[Extra] Fake caption embedding + upsert...")
        fake_caption = "This frame shows a cultural heritage artifact"
        from agent.video_ingest import _build_video_metadata, _upsert_nodes_to_qdrant
        from llama_index.core.schema import TextNode
        import uuid
        seg = {"text": fake_caption, "start": 1.0, "end": 3.0}
        meta = _build_video_metadata(seg, video_path, f"file://{video_path}", "visual_caption")
        vec = embedder.get_text_embedding(fake_caption)
        node = TextNode(text=fake_caption, metadata=meta, id_=str(uuid.uuid4()))
        node.embedding = vec
        _upsert_nodes_to_qdrant([node], client)
        print(f"      Fake caption upserted")

        # 8. Verify the fake caption is in Qdrant
        all_chunks = client.scroll(
            collection_name=TEST_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="source_name", match=MatchValue(value="dry_test.mp4"))]
            ),
            limit=50,
            with_payload=True,
        )[0]
        modalities = {}
        for p in all_chunks:
            mod = p.payload.get("modality", "unknown")
            modalities[mod] = modalities.get(mod, 0) + 1
        print(f"      All chunks: {modalities}")
        assert modalities.get("visual_caption", 0) > 0, "Fake caption not found"
        assert modalities.get("audio_transcript", 0) > 0, "Audio chunk not found"

    print("=" * 60)
    print("✅ PHASE B DRY-RUN PASSED")
    print("=" * 60)
    print(f"\nWhat was verified:")
    print(f"  - Scene detection: working ({len(scenes)} scene(s))")
    print(f"  - Frame extraction + OCR: working")
    print(f"  - Audio chunk indexing: {n_audio}")
    print(f"  - Dedup similarity check: working")
    print(f"  - Fake visual caption upsert: working")
    print(f"\nTo test with GLM-4V captions:")
    print(f"  python tests/test_video_phase_b.py")

if __name__ == "__main__":
    try:
        test_phase_b_dry()
    finally:
        teardown_collection(QdrantClient(url="http://localhost:6333"))
