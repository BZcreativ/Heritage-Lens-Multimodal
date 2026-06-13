"""
Video ingestion module for Heritage Lens Multimodal Agent.

Phase A: Audio transcription with faster-whisper → timestamped chunks → Qdrant
Phase B: Scene detection + visual captioning + OCR (with deduplication)

All video-derived text chunks are embedded with all-MiniLM-L6-v2 (384-dim)
and upserted into the SAME text collection (heritage_lens_text) so the
existing retrieval, generator, and judge layers work unchanged.
"""

import os
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct, VectorParams, Distance, Filter, FieldCondition,
    MatchValue, Range, PayloadSchemaType
)
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

from faster_whisper import WhisperModel

# ── Constants ────────────────────────────────────────────────────────────────
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
# Overridable so tests can target a throwaway collection instead of production.
TEXT_COLLECTION = os.getenv("HL_TEXT_COLLECTION", "heritage_lens_text")
AUDIO_SAMPLE_RATE = 16000
DEDUP_THRESHOLD = 0.92        # cosine similarity skip threshold
DEDUP_TIME_WINDOW = 5.0     # seconds around segment to search for dupes
# Whisper model overridable so CPU-only hosts can trade quality for speed
# (e.g. HL_WHISPER_MODEL=medium). Default large-v3 is best for Italian/Spanish.
WHISPER_MODEL = os.getenv("HL_WHISPER_MODEL", "large-v3")
# Speech-to-text backend: "parakeet" (NVIDIA Parakeet v3 via onnx-asr — multilingual
# incl. it/es, ~half the RAM of whisper large-v3, default) or "whisper" (faster-whisper).
# Parakeet falls back to whisper automatically if it fails to load/transcribe.
PARAKEET_MODEL = os.getenv("HL_PARAKEET_MODEL", "nemo-parakeet-tdt-0.6b-v3")
PARAKEET_QUANT = os.getenv("HL_PARAKEET_QUANT", "int8")
# Visual frame sampling: sample one frame per FRAME_INTERVAL seconds within a
# scene (capped), instead of a single mid-frame, so long single-shot videos get
# more than one caption. Short scenes (span <= interval) still yield one frame.
FRAME_INTERVAL = float(os.getenv("HL_FRAME_INTERVAL", "90"))
MAX_FRAMES_PER_SCENE = int(os.getenv("HL_MAX_FRAMES_PER_SCENE", "8"))

# ── Embedding / model singletons ─────────────────────────────────────────────
# Loaded once per process and reused across videos (corpus ingestion reloaded
# these per file previously, which was the main batch-ingest cost).
_EMBEDDER = None
_WHISPER = None
_PARAKEET = None


def _get_embedder():
    """Return the SAME embedder used by the text pipeline (cached)."""
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    return _EMBEDDER


def _get_whisper(model_name: str = WHISPER_MODEL):
    """Return a cached faster-whisper model (loaded once per process)."""
    global _WHISPER
    if _WHISPER is None:
        device = "cuda" if _has_gpu() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        _WHISPER = WhisperModel(model_name, device=device, compute_type=compute_type)
    return _WHISPER


def _has_gpu() -> bool:
    """True if an NVIDIA GPU is visible. Fixed command, no user input."""
    import shutil
    if not shutil.which("nvidia-smi"):
        return False
    return subprocess.run(["nvidia-smi"], capture_output=True).returncode == 0


def _get_parakeet():
    """Cached Parakeet v3 ASR adapter (onnx-asr) with Silero VAD + timestamps.

    VAD segments long audio into speech chunks (the model handles ~30s at a time)
    and yields absolute start/end per segment — so it maps directly onto our
    transcript-segment shape, multilingually, at ~half the RAM of whisper large-v3.
    """
    global _PARAKEET
    if _PARAKEET is None:
        import onnx_asr
        model = onnx_asr.load_model(PARAKEET_MODEL, quantization=PARAKEET_QUANT)
        vad = onnx_asr.load_vad("silero")
        _PARAKEET = model.with_vad(vad).with_timestamps()
    return _PARAKEET


def _transcribe_parakeet(audio_path: str) -> List[Dict[str, Any]]:
    """Transcribe with Parakeet v3. Returns the same shape as the whisper path."""
    asr = _get_parakeet()
    results = []
    for seg in asr.recognize(audio_path):
        text = (seg.text or "").strip()
        if not text:
            continue
        results.append({
            "text": text,
            "start": round(float(seg.start), 2),
            "end": round(float(seg.end), 2),
            "language": "unknown",  # onnx-asr does not surface detected language
        })
    return results


def _transcribe_whisper(audio_path: str, model_name: str = WHISPER_MODEL) -> List[Dict[str, Any]]:
    """Transcribe with faster-whisper (fallback backend)."""
    model = _get_whisper(model_name)
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=None,          # auto-detect; handles Italian/Spanish
        vad_filter=True,        # skip non-speech
    )
    results = []
    for seg in segments:
        results.append({
            "text": seg.text.strip(),
            "start": round(float(seg.start), 2),
            "end": round(float(seg.end), 2),
            "language": info.language or "unknown",
        })
    return results


def _sample_timestamps(start: float, end: float, interval: float, max_frames: int) -> List[float]:
    """Frame sample times within [start, end]: a single mid-point for short
    scenes, otherwise evenly spaced points roughly `interval` seconds apart."""
    span = end - start
    if interval <= 0 or span <= interval:
        return [round((start + end) / 2, 2)]
    n = min(max_frames, max(1, int(span // interval)))
    step = span / n
    return [round(start + step * (i + 0.5), 2) for i in range(n)]


def _split_scene(start: float, end: float, interval: float, max_frames: int) -> List[tuple]:
    """Turn a scene into one (t, t) point-in-time sub-scene per sampled frame."""
    return [(t, t) for t in _sample_timestamps(start, end, interval, max_frames)]


def _video_point_id(video_id: str, modality: str, start, end, text: str) -> str:
    """Deterministic point ID keyed on video content.

    Re-indexing the same video produces the same IDs, so upserts overwrite in
    place instead of creating duplicate chunks.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}|{modality}|{start}|{end}|{text}"))


# ── Audio extraction ──────────────────────────────────────────────────────────

def extract_audio(video_path: str, output_dir: Optional[str] = None) -> str:
    """Extract mono 16kHz WAV audio from video using ffmpeg."""
    video_path = Path(video_path)
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    audio_path = Path(output_dir) / f"{video_path.stem}_audio.wav"

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", str(AUDIO_SAMPLE_RATE), "-ac", "1",
        str(audio_path),
    ], check=True, capture_output=True)
    return str(audio_path)


# ── Transcription ───────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str, model_name: str = WHISPER_MODEL) -> List[Dict[str, Any]]:
    """
    Transcribe audio. Backend selected by HL_ASR_BACKEND ("parakeet" default, or "whisper").
    Parakeet falls back to whisper if it fails. Returns list of {text, start, end, language}.
    """
    backend = os.getenv("HL_ASR_BACKEND", "parakeet").lower()
    if backend == "parakeet":
        try:
            return _transcribe_parakeet(audio_path)
        except Exception as e:
            print(f"[video_ingest] Parakeet ASR failed ({e}); falling back to whisper")
    return _transcribe_whisper(audio_path, model_name)


# ── Deduplication helper ────────────────────────────────────────────────────

def _find_similar_chunk(
    qdrant_client: QdrantClient,
    vector: List[float],
    video_id: str,
    start: float,
    end: float,
    threshold: float = DEDUP_THRESHOLD,
) -> bool:
    """
    Search within a time window of the same video for a chunk whose vector
    is ≥ threshold cosine-similar. Used in Phase B to skip near-duplicate
    visual/OCR chunks against existing audio transcripts.
    """
    try:
        from qdrant_client.http.models import QueryRequest
        results = qdrant_client.query_points(
            collection_name=TEXT_COLLECTION,
            query=vector,
            limit=5,
            query_filter=Filter(
                must=[
                    FieldCondition(key="video_id", match=MatchValue(value=video_id)),
                    FieldCondition(
                        key="start",
                        range=Range(
                            gte=max(0.0, start - DEDUP_TIME_WINDOW),
                            lte=end + DEDUP_TIME_WINDOW,
                        ),
                    ),
                ]
            ),
            with_payload=False,
        ).points
        for r in results:
            if r.score >= threshold:
                return True
        return False
    except Exception as e:
        # If Qdrant payload indexes are missing, fall back to non-filtered query
        results = qdrant_client.query_points(
            collection_name=TEXT_COLLECTION,
            query=vector,
            limit=20,
            with_payload=True,
        ).points
        for r in results:
            payload = r.payload or {}
            if payload.get("video_id") == video_id:
                r_start = payload.get("start", -9999)
                r_end = payload.get("end", -9999)
                if abs(r_start - start) <= DEDUP_TIME_WINDOW or abs(r_end - end) <= DEDUP_TIME_WINDOW:
                    if r.score >= threshold:
                        return True
        return False


# ── Chunk creation ──────────────────────────────────────────────────────────

def _build_video_metadata(
    segment: Dict[str, Any],
    video_path: str,
    video_url: Optional[str],
    modality: str,
) -> Dict[str, Any]:
    """Construct the payload metadata for a video-derived chunk."""
    video_id = Path(video_path).stem
    source_name = Path(video_path).name
    return {
        "source_name": source_name,
        "source_type": "video",
        "institution": "unknown",
        "cultural_perspective": "unknown",
        "language_of_origin": segment.get("language", "unknown"),
        "author": "unknown",
        "page_number": "N/A",
        "modality": modality,
        "video_id": video_id,
        "video_url": video_url or str(video_path),
        "start": segment["start"],
        "end": segment["end"],
    }


def _nodes_from_segments(
    segments: List[Dict[str, Any]],
    video_path: str,
    video_url: Optional[str],
    modality: str,
    embedder,
) -> List[TextNode]:
    """Turn transcript/caption/OCR segments into LlamaIndex TextNodes."""
    nodes = []
    for seg in segments:
        text = seg["text"]
        if not text or len(text) < 3:
            continue
        meta = _build_video_metadata(seg, video_path, video_url, modality)
        node = TextNode(
            text=text,
            metadata=meta,
            id_=_video_point_id(meta["video_id"], modality, seg["start"], seg["end"], text),
        )
        node.embedding = embedder.get_text_embedding(text)
        nodes.append(node)
    return nodes


# ── Indexing helpers ────────────────────────────────────────────────────────

def _ensure_payload_indexes(qdrant_client: QdrantClient):
    """Create payload indexes for video fields if they don't exist."""
    try:
        qdrant_client.create_payload_index(
            TEXT_COLLECTION, "video_id", PayloadSchemaType.KEYWORD
        )
    except Exception:
        pass
    try:
        qdrant_client.create_payload_index(
            TEXT_COLLECTION, "modality", PayloadSchemaType.KEYWORD
        )
    except Exception:
        pass
    try:
        qdrant_client.create_payload_index(
            TEXT_COLLECTION, "start", PayloadSchemaType.FLOAT
        )
    except Exception:
        pass


def _upsert_nodes_to_qdrant(nodes: List[TextNode], qdrant_client: QdrantClient):
    """
    Upsert TextNodes directly into Qdrant.
    We bypass LlamaIndex's re-embedding because node.embedding is already set.
    """
    points = []
    for node in nodes:
        points.append(PointStruct(
            id=node.id_ or str(uuid.uuid4()),
            vector=node.embedding,
            payload={
                "text": node.text,
                **node.metadata,
            },
        ))
        if len(points) >= 50:
            qdrant_client.upsert(collection_name=TEXT_COLLECTION, points=points)
            points = []
    if points:
        qdrant_client.upsert(collection_name=TEXT_COLLECTION, points=points)


# ── Public API: Phase A — Audio transcript ───────────────────────────────────

def index_video_audio(
    video_path: str,
    qdrant_client: QdrantClient,
    video_url: Optional[str] = None,
) -> int:
    """
    Extract audio, transcribe, chunk, embed, and upsert into heritage_lens_text.
    Returns number of chunks indexed.
    """
    video_path = str(Path(video_path).resolve())
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    _ensure_payload_indexes(qdrant_client)

    # 1. Extract audio
    audio_path = extract_audio(video_path)

    # 2. Transcribe
    segments = transcribe_audio(audio_path)
    if not segments:
        print(f"[video_ingest] No speech detected in {video_path}")
        return 0

    # 3. Embed + chunk
    embedder = _get_embedder()
    nodes = _nodes_from_segments(
        segments, video_path, video_url, modality="audio_transcript", embedder=embedder
    )

    # 4. Upsert
    _upsert_nodes_to_qdrant(nodes, qdrant_client)

    # 5. Cleanup temp audio
    try:
        os.remove(audio_path)
    except Exception:
        pass

    print(f"[video_ingest] Indexed {len(nodes)} audio transcript chunks from {Path(video_path).name}")
    return len(nodes)


# ── Public API: Phase B — Visual captions + OCR ─────────────────────────────

CAPTION_PROMPT = (
    "Describe this frame from a cultural heritage video in one concise sentence. "
    "Focus on artifacts, architecture, text visible on screen, and cultural context."
)


def _caption_frame(img, glm_client, openai_client) -> str:
    """Caption one frame via GLM-4.5V (primary) then GPT-4o (fallback). Returns '' on failure."""
    import base64
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    content = [
        {"type": "text", "text": CAPTION_PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]
    if glm_client:
        try:
            resp = glm_client.chat.completions.create(
                model="glm-4.5v",
                messages=[{"role": "user", "content": content}],
                max_tokens=150,
                temperature=0.3,
                # glm-4.5v is a reasoning model; without this the token budget is
                # consumed by reasoning_content and `content` comes back empty.
                extra_body={"thinking": {"type": "disabled"}},
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text
        except Exception as e:
            print(f"[video_ingest] GLM-4V caption failed: {e}")
    if openai_client:
        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": content}],
                max_tokens=150,
                temperature=0.3,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[video_ingest] GPT-4o caption failed: {e}")
    return ""


def index_video_visual(
    video_path: str,
    qdrant_client: QdrantClient,
    video_url: Optional[str] = None,
    use_glm_caption: bool = True,
    use_gpt4o_caption: bool = False,
) -> Dict[str, int]:
    """
    Detect scenes, caption representative frames, OCR them, and upsert.
    Skips chunks that are too similar (≥0.92 cosine) to existing chunks in the
    same video_id + time window.

    Returns {"caption": N, "ocr": M, "skipped": K}.
    """
    from PIL import Image
    import pytesseract

    video_path = str(Path(video_path).resolve())
    video_id = Path(video_path).stem
    source_name = Path(video_path).name

    _ensure_payload_indexes(qdrant_client)
    embedder = _get_embedder()

    # 1. Detect scenes with PySceneDetect (try; skip if not installed)
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        from scenedetect.backends import VideoStreamCv2
    except ImportError:
        print(f"[video_ingest] PySceneDetect not installed; skipping visual indexing for {source_name}")
        return {"caption": 0, "ocr": 0, "skipped": 0, "errors": 0}

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    if not scene_list:
        # PySceneDetect returns [] when there are no cuts (e.g. a single static
        # shot or talking head). Treat the whole video as one scene so we still
        # caption/OCR a representative frame instead of skipping visual indexing.
        duration = video.duration
        if duration is None or duration.get_seconds() <= 0:
            print(f"[video_ingest] No scenes and no duration for {source_name}; skipping visual indexing")
            return {"caption": 0, "ocr": 0, "skipped": 0, "errors": 0}
        scene_list = [(video.base_timecode, duration)]
        print(f"[video_ingest] No cuts detected; treating whole video as one scene "
              f"({duration.get_seconds():.1f}s) for {source_name}")

    # Normalize to (start_sec, end_sec) floats and split long scenes into several
    # sample points, so a long single-shot video yields multiple frames not one.
    sampled_scenes = []
    for sc in scene_list:
        sampled_scenes.extend(
            _split_scene(sc[0].get_seconds(), sc[1].get_seconds(), FRAME_INTERVAL, MAX_FRAMES_PER_SCENE)
        )
    scene_list = sampled_scenes

    # 2. Load vision models (SigLIP for embeddings if needed, but we use all-MiniLM for text)
    #    For captioning: GLM-4V (primary) or GPT-4o vision (fallback)
    caption_model = None
    caption_processor = None
    if not use_glm_caption and not use_gpt4o_caption:
        try:
            from transformers import AutoProcessor, AutoModelForVision2Seq
            caption_processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            caption_model = AutoModelForVision2Seq.from_pretrained("Salesforce/blip-image-captioning-base")
            caption_model.eval()
        except Exception as e:
            print(f"[video_ingest] Local caption model failed: {e}; will use GLM-4V if available")
            use_glm_caption = True

    # 3. GLM client (primary vision API for this project)
    glm_client = None
    if use_glm_caption:
        try:
            from openai import OpenAI
            glm_api_key = os.getenv("GLM_API_KEY")
            if glm_api_key:
                glm_client = OpenAI(
                    api_key=glm_api_key,
                    base_url="https://api.z.ai/api/paas/v4",
                )
                print("[video_ingest] GLM-4V client initialized")
            else:
                print("[video_ingest] GLM_API_KEY not set; falling back to GPT-4o vision")
                use_gpt4o_caption = True
        except Exception as e:
            print(f"[video_ingest] GLM client init failed: {e}")
            use_gpt4o_caption = True

    # 4. OpenAI client for GPT-4o vision (fallback)
    openai_client = None
    if use_gpt4o_caption:
        try:
            from openai import OpenAI
            openai_client = OpenAI()
        except Exception as e:
            print(f"[video_ingest] OpenAI client init failed: {e}")
            openai_client = None

    # OCR language: the corpus is Italian/Spanish, so default beyond eng.
    # Filter to whatever tesseract packs are actually installed to avoid errors.
    ocr_lang = os.getenv("HL_OCR_LANG", "eng+ita+spa")
    try:
        avail = set(pytesseract.get_languages(config=""))
        ocr_lang = "+".join([l for l in ocr_lang.split("+") if l in avail]) or "eng"
    except Exception:
        ocr_lang = "eng"

    stats = {"caption": 0, "ocr": 0, "skipped": 0, "errors": 0}
    with tempfile.TemporaryDirectory() as tmpdir:
        for scene_idx, scene in enumerate(scene_list):
            start_sec, end_sec = scene
            mid_sec = round((start_sec + end_sec) / 2, 2)

            # Extract frame at mid-point
            frame_path = Path(tmpdir) / f"scene_{scene_idx:04d}.png"
            try:
                subprocess.run([
                    "ffmpeg", "-y",
                    "-ss", str(mid_sec),
                    "-i", video_path,
                    "-vframes", "1", "-q:v", "2",
                    str(frame_path),
                ], check=True, capture_output=True)
            except Exception as e:
                print(f"[video_ingest] Frame extraction failed at {mid_sec}s: {e}")
                continue

            img = Image.open(frame_path).convert("RGB")

            # ── Caption ─────────────────────────────────────────────────────
            caption_text = _caption_frame(img, glm_client, openai_client)
            if not caption_text and caption_model and caption_processor:
                try:
                    import torch
                    inputs = caption_processor(images=img, return_tensors="pt")
                    with torch.no_grad():
                        out = caption_model.generate(**inputs, max_new_tokens=50)
                    caption_text = caption_processor.decode(out[0], skip_special_tokens=True).strip()
                except Exception as e:
                    print(f"[video_ingest] Local caption failed: {e}")

            # A captioner was configured but produced nothing for this frame —
            # surface it so a fully-failing run (bad model/key) isn't silently
            # reported as "0 captions" the way the glm-4v model-name bug was.
            if (glm_client or openai_client or (caption_model and caption_processor)) and not caption_text:
                stats["errors"] += 1
                print(f"[video_ingest] All caption methods failed for frame at {start_sec}s")

            if caption_text and len(caption_text) > 5:
                seg = {"text": caption_text, "start": start_sec, "end": end_sec}
                meta = _build_video_metadata(seg, video_path, video_url, "visual_caption")
                vec = embedder.get_text_embedding(caption_text)

                if _find_similar_chunk(qdrant_client, vec, video_id, start_sec, end_sec):
                    stats["skipped"] += 1
                    print(f"[video_ingest] Skipped duplicate caption at {start_sec}s")
                else:
                    node = TextNode(text=caption_text, metadata=meta,
                                    id_=_video_point_id(video_id, "visual_caption", start_sec, end_sec, caption_text))
                    node.embedding = vec
                    _upsert_nodes_to_qdrant([node], qdrant_client)
                    stats["caption"] += 1

            # ── OCR ───────────────────────────────────────────────────────────
            try:
                ocr_text = pytesseract.image_to_string(img, lang=ocr_lang).strip()
            except Exception:
                ocr_text = ""

            if ocr_text and len(ocr_text) > 3:
                seg = {"text": ocr_text, "start": start_sec, "end": end_sec}
                meta = _build_video_metadata(seg, video_path, video_url, "ocr_text")
                vec = embedder.get_text_embedding(ocr_text)

                if _find_similar_chunk(qdrant_client, vec, video_id, start_sec, end_sec):
                    stats["skipped"] += 1
                    print(f"[video_ingest] Skipped duplicate OCR at {start_sec}s")
                else:
                    node = TextNode(text=ocr_text, metadata=meta,
                                    id_=_video_point_id(video_id, "ocr_text", start_sec, end_sec, ocr_text))
                    node.embedding = vec
                    _upsert_nodes_to_qdrant([node], qdrant_client)
                    stats["ocr"] += 1

    print(f"[video_ingest] Visual indexing done for {source_name}: {stats}")
    return stats


# ── Batch / convenience helpers ─────────────────────────────────────────────

def index_video(
    video_path: str,
    qdrant_client: QdrantClient,
    video_url: Optional[str] = None,
    index_audio: bool = True,
    index_visual: bool = False,
    use_glm_caption: bool = True,
) -> Dict[str, Any]:
    """
    Full video indexing entry point.

    Args:
        video_path: Path to video file.
        qdrant_client: Qdrant client instance.
        video_url: Public URL for the video (e.g. S3/MinIO). If None, uses local path.
        index_audio: Run Phase A (transcription).
        index_visual: Run Phase B (scene captions + OCR).
        use_glm_caption: Use GLM-4V for frame captions (default True).
    """
    results = {"audio_chunks": 0, "visual": {"caption": 0, "ocr": 0, "skipped": 0, "errors": 0}}
    if index_audio:
        results["audio_chunks"] = index_video_audio(video_path, qdrant_client, video_url)
    if index_visual:
        results["visual"] = index_video_visual(video_path, qdrant_client, video_url, use_glm_caption=use_glm_caption)
    return results


def index_videos_in_corpus(
    corpus_dir: str,
    qdrant_client: QdrantClient,
    video_url_base: Optional[str] = None,
    index_audio: bool = True,
    index_visual: bool = False,
    use_glm_caption: bool = True,
):
    """
    Scan corpus_dir for video files and index all of them.
    """
    VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        print(f"[video_ingest] Corpus dir not found: {corpus_dir}")
        return

    for video_path in corpus_path.iterdir():
        if video_path.suffix.lower() in VIDEO_EXTS:
            video_url = None
            if video_url_base:
                video_url = f"{video_url_base.rstrip('/')}/{video_path.name}"
            index_video(
                str(video_path),
                qdrant_client,
                video_url=video_url,
                index_audio=index_audio,
                index_visual=index_visual,
                use_glm_caption=use_glm_caption,
            )


if __name__ == "__main__":
    # Quick smoke test: requires a video file at argv[1]
    import sys
    if len(sys.argv) < 2:
        print("Usage: python video_ingest.py <video_path>")
        sys.exit(1)
    client = QdrantClient(url="http://localhost:6333")
    n = index_video_audio(sys.argv[1], client)
    print(f"Indexed {n} audio transcript chunks.")
