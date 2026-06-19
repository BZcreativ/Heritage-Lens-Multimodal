"""Unit tests for the pure parsing helpers — no DB / pipeline needed.

Run:  pytest api/tests/test_parsing.py
"""
from api import parsing


SAMPLE_L3 = """⚠️ SOURCE BIAS
3 of 4 sources are Western academic papers from Italian university presses.

📄 ABSENCES
No indigenous oral traditions or local community knowledge are present.

🕵️ INTERPRETIVE LIMITS
The term 'ritual' reflects an academic classification, not an emic category.

⚠️ CONFIDENCE
Moderate. Iconographic support is strong but structural claims are weak.
"""


def test_split_layer3_four_sections():
    s = parsing.split_layer3(SAMPLE_L3)
    assert "Western academic" in s["⚠️ SOURCE BIAS"]
    assert "indigenous oral traditions" in s["📄 ABSENCES"]
    assert "academic classification" in s["🕵️ INTERPRETIVE LIMITS"]
    assert "Moderate" in s["⚠️ CONFIDENCE"]


def test_split_layer3_tolerates_markdown():
    raw = "**⚠️ SOURCE BIAS**\nbiased.\n## 📄 ABSENCES\ngaps."
    s = parsing.split_layer3(raw)
    assert s["⚠️ SOURCE BIAS"] == "biased."
    assert s["📄 ABSENCES"] == "gaps."


def test_confidence_heuristic():
    assert parsing.confidence_from_text("Moderate. mixed.").level == "moderate"
    assert parsing.confidence_from_text("High confidence, robust.").level == "high"
    assert parsing.confidence_from_text("Very low; insufficient data.").level == "low"
    assert parsing.confidence_from_text("Moderate.").segments == 3


def test_build_sources_dedup_and_type():
    chunks = [
        {"text": "a", "score": 0.9, "metadata": {
            "source_name": "Doc A.pdf", "author": "X", "page_number": "12",
            "source_type": "book", "institution": "Inst"}},
        {"text": "b", "score": 0.5, "metadata": {
            "source_name": "Doc A.pdf", "author": "X", "page_number": "13"}},
        {"text": "c", "score": 0.8, "metadata": {
            "source_name": "Lecture.mp4", "modality": "audio_transcript",
            "start": 120, "end": 249}},
    ]
    sources = parsing.build_sources(chunks)
    assert len(sources) == 2                         # Doc A deduped
    doc_a = next(s for s in sources if s.title == "Doc A.pdf")
    assert doc_a.type == "pdf"
    assert doc_a.meta["Chunks used"] == "2"
    lecture = next(s for s in sources if s.title == "Lecture.mp4")
    assert lecture.type == "vid"
    assert "120s – 249s" in lecture.subtitle


def test_build_video_chunks_filters_modality():
    chunks = [
        {"text": "spoken words", "metadata": {
            "modality": "audio_transcript", "start": 1, "end": 5,
            "source_name": "v.mp4", "video_url": "http://x/v.mp4"}},
        {"text": "plain pdf text", "metadata": {"source_name": "d.pdf", "page_number": "1"}},
    ]
    vids = parsing.build_video_chunks(chunks)
    assert len(vids) == 1
    assert vids[0].video_url == "http://x/v.mp4"     # http → seekable
    assert vids[0].timestamp == "1s – 5s"


# ----------------------------------------------------------- sources view ----

def test_dedup_corpus_sources_collapses_and_counts():
    payloads = [
        {"source_name": "Doc A.pdf", "author": "X", "source_type": "book",
         "institution": "Inst", "language_of_origin": "italian"},
        {"source_name": "Doc A.pdf", "author": "X"},                 # same source
        {"source_name": "Doc B.pdf", "author": "Y", "modality": "audio_transcript"},
        {"author": "no source name — skipped"},
    ]
    out = parsing.dedup_corpus_sources(payloads)
    assert len(out) == 2
    a = next(s for s in out if s.source_name == "Doc A.pdf")
    assert a.chunk_count == 2
    assert a.source_type == "book" and a.institution == "Inst"
    # sorted by chunk_count desc → Doc A (2) before Doc B (1)
    assert out[0].source_name == "Doc A.pdf"


# ----------------------------------------------------------- upload names ----

def test_safe_corpus_filename_accepts_and_strips_paths():
    assert parsing.safe_corpus_filename("paper.pdf") == "paper.pdf"
    assert parsing.safe_corpus_filename("clip.MP4") == "clip.MP4"
    # path components stripped (traversal defence), basename kept
    assert parsing.safe_corpus_filename("../../etc/evil.pdf") == "evil.pdf"
    assert parsing.safe_corpus_filename("C:\\temp\\scan.png") == "scan.png"


def test_safe_corpus_filename_rejects_bad():
    assert parsing.safe_corpus_filename("notes.txt") is None        # unsupported ext
    assert parsing.safe_corpus_filename("noext") is None
    assert parsing.safe_corpus_filename("") is None
    assert parsing.safe_corpus_filename(None) is None
    assert parsing.safe_corpus_filename("../..") is None
