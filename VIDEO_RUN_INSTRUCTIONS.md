# Video Indexing + Timestamped Search — Run Instructions

## What Was Added

| File | Purpose |
|------|---------|
| `agent/video_ingest.py` | **Phase A**: Audio transcription (faster-whisper) → timestamped chunks → Qdrant. **Phase B**: Scene detection, frame captioning (GPT-4o vision), OCR, with deduplication. |
| `tests/test_video_ingest.py` | End-to-end verification: synthetic video → index → query → assert timestamp + metadata. |
| `agent/ingest.py` (updated) | Wires `video_ingest.index_videos_in_corpus()` into the corpus rebuild flow. |
| `agent/generator.py` (updated) | Layer 2 now shows `Timestamp` instead of `Page` for video chunks. Layer 3 analyzes `modality` counts as provenance signals. |
| `ui/app.py` (updated) | Sidebar shows 🎬 Video chunk count. Search results show a **Video Evidence** gallery with modality badges, timestamps, and deep-link seek buttons. |
| `requirements.txt` (updated) | Added `faster-whisper>=1.0.0` and `scenedetect>=0.6.2`. |

---

## Prerequisites

1. **Qdrant running** at `localhost:6333` (existing setup)
2. **ffmpeg** installed (system binary — already on this server)
3. **espeak-ng** installed (for test script only — already installed)
4. **Python 3.10+** with the project venv activated

---

## Quick Start

### 1. Activate environment
```bash
cd /home/heritage/heritage-lens-multimodal
source venv/bin/activate
```

### 2. Verify dependencies
```bash
python -c "import faster_whisper; print(faster_whisper.__version__)"
# Expected: 1.x.x
```

### 3. Run the test (creates a synthetic video, indexes it, queries it)
```bash
python tests/test_video_ingest.py
```

Expected output:
```
============================================================
VIDEO INGESTION + TIMESTAMPED SEARCH TEST
============================================================
[1/4] Creating synthetic video at /tmp/.../test_video.mp4...
      Video created: 55154 bytes
[2/4] Indexing audio transcript...
[video_ingest] Indexed 1 audio transcript chunks from test_video.mp4
      Indexed 1 audio transcript chunks
[3/4] Querying: 'obsidian blade ritual La Venta'
Balanced retrieval active across 3 sources: [...]
      Retrieved 5 chunks
[4/4] Verifying chunk metadata...
      Chunk 0: modality=audio_transcript, start=0.0, end=4.4, source=test_video.mp4
============================================================
✅ ALL TESTS PASSED
============================================================
```

### 4. Ingest a real video into the corpus
```bash
# Copy your video into the corpus directory
cp /path/to/your_video.mp4 data/corpus/

# Rebuild the entire index (PDFs + images + video transcripts)
python -c "from agent.ingest import initialize_vector_db; initialize_vector_db()"
```

This will:
- Re-index all PDFs (unchanged behavior)
- Re-index all images (unchanged behavior)
- **NEW**: Extract audio, transcribe with faster-whisper, and index transcript chunks with timestamps into `heritage_lens_text`

### 5. Launch the UI and search
```bash
streamlit run ui/app.py
```

Upload a video via the sidebar **📁 Add to Corpus** → click **Process & Index** → search with a query. Video results appear in the **🎬 Video Evidence** gallery with:
- **Modality badge** (`audio_transcript`, `visual_caption`, or `ocr_text`)
- **Timestamp range** (e.g., `⏱ 12.5s – 18.3s`)
- **Seek link** if `video_url` is an HTTP URL

---

## Configuration

### Video URL / Object Storage
By default, `video_url` is set to the local file path. To use object storage (S3, MinIO, etc.), set the base URL in `config/settings.yaml` or pass it directly:

```python
from agent.video_ingest import index_video_audio
index_video_audio("data/corpus/my_video.mp4", qdrant_client, video_url="https://cdn.example.com/my_video.mp4")
```

### Whisper Model Size
Edit `agent/video_ingest.py`:
```python
WHISPER_MODEL = "large-v3"   # default, multilingual, best quality
# WHISPER_MODEL = "medium"   # faster, slightly less accurate
# WHISPER_MODEL = "small"      # fastest, good for English-only
```

### Deduplication Threshold (Phase B)
Edit `agent/video_ingest.py`:
```python
DEDUP_THRESHOLD = 0.92   # cosine similarity — skip if ≥ this
DEDUP_TIME_WINDOW = 5.0  # seconds around segment to search for dupes
```

---

## Phase B: Visual Captioning + OCR

Phase B is implemented in `agent/video_ingest.py` but **disabled by default** in the corpus rebuild. To enable it:

```python
from agent.video_ingest import index_videos_in_corpus
index_videos_in_corpus(
    "data/corpus",
    qdrant_client,
    index_audio=True,    # Phase A
    index_visual=True,   # Phase B ← enable this
)
```

Phase B requires:
- `scenedetect` (Python package, listed in `requirements.txt`)
- GPT-4o vision access (for captions) — uses existing OpenAI client
- `pytesseract` (already installed) — for OCR

The deduplication guard will automatically skip visual/OCR chunks that are >92% similar to existing audio transcript chunks in the same time window, preventing inflated source counts.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No space left on device` during faster-whisper model download | Clear pip/huggingface cache: `pip cache purge; rm -rf ~/.cache/huggingface/*` |
| `ffmpeg error` | Ensure ffmpeg is installed: `ffmpeg -version` |
| `espeak-ng not found` (test only) | `sudo apt-get install espeak-ng` |
| Video chunks not appearing in UI | Check Qdrant count: `python -c "from qdrant_client import QdrantClient; print(QdrantClient('http://localhost:6333').count('heritage_lens_text').count)"` |
| Retrieval returns 0 video chunks | The query may not match the transcript text. Try querying a word you know was spoken. |

---

*Last updated: 2026-06-12*
