import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
import base64
import yaml

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(workspace_dir)

# Load settings from config/settings.yaml
_settings = {}
_settings_path = os.path.join(workspace_dir, "config", "settings.yaml")
if os.path.exists(_settings_path):
    with open(_settings_path) as _f:
        _settings = yaml.safe_load(_f) or {}
MAX_IMAGES = _settings.get("ui", {}).get("max_display_images", 3)
UI_TITLE   = _settings.get("ui", {}).get("title", "Heritage Lens Multimodal Agent")

# Rebuild Qdrant index if collections are empty
def _qdrant_text_count():
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(url="http://localhost:6333").get_collection("heritage_lens_text").points_count
    except Exception:
        return 0

def _qdrant_video_chunk_count():
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchAny
        client = QdrantClient(url="http://localhost:6333")
        return client.count(
            collection_name="heritage_lens_text",
            count_filter=Filter(
                must=[FieldCondition(key="modality", match=MatchAny(any=["audio_transcript", "visual_caption", "ocr_text"]))]
            ),
        ).count
    except Exception:
        return 0

if _qdrant_text_count() == 0:
    print("Qdrant text collection empty — rebuilding from PDFs...")
    from agent.ingest import initialize_vector_db
    try:
        initialize_vector_db()
    except Exception as e:
        print(f"Ingestion failed: {e}")

from agent.env_loader import load_env
load_env()


def img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def main():
    st.set_page_config(layout="wide", page_title=UI_TITLE)

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif !important;
            color: #F8FAFC;
        }

        [data-testid="stAppViewContainer"] {
            background-color: #020617;
            background-image:
                radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.1), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.1), transparent 25%);
            color: #F8FAFC;
        }

        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.5) !important;
            backdrop-filter: blur(10px);
        }

        #MainMenu { visibility: hidden; }
        footer     { visibility: hidden; }

        @keyframes slideUpFade {
            0%   { opacity: 0; transform: translateY(30px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0)    scale(1);    }
        }

        .panel {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(16px);
            padding: 32px;
            border-radius: 20px;
            min-height: 550px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.08);
            transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
            animation: slideUpFade 0.6s ease-out forwards;
            opacity: 0;
            color: #E2E8F0;
        }
        div[data-testid="column"]:nth-of-type(1) .panel  { animation-delay: 0.1s; }
        div[data-testid="column"]:nth-of-type(2) .panel  { animation-delay: 0.2s; }
        div[data-testid="column"]:nth-of-type(3) .panel-blue { animation-delay: 0.3s; }

        .panel:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.15);
            background: rgba(30,41,59,0.8);
        }

        .panel-blue {
            background: linear-gradient(135deg, #7DD3FC 0%, #38BDF8 100%);
            padding: 32px;
            border-radius: 20px;
            min-height: 550px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 25px -5px rgba(14,165,233,0.3), inset 0 2px 4px 0 rgba(255,255,255,0.6);
            border: 1px solid #BAE6FD;
            transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
            animation: slideUpFade 0.6s ease-out forwards;
            opacity: 0;
            color: #082F49;
        }
        .panel-blue:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 25px -5px rgba(14,165,233,0.5), inset 0 2px 4px 0 rgba(255,255,255,0.8);
            filter: brightness(1.05);
        }

        .panel-content {
            flex-grow: 1;
            font-size: 1.1rem;
            line-height: 1.7;
        }

        .header-box {
            background: rgba(15,23,42,0.7);
            backdrop-filter: blur(20px);
            padding: 32px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            border-radius: 20px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.05);
            animation: slideUpFade 0.6s ease-out forwards;
        }
        .header-box h2 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(to right, #F8FAFC, #94A3B8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.025em;
        }
        .header-box p {
            margin: 0;
            color: #38BDF8;
            font-size: 1.1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .image-gallery-card {
            background: rgba(15,23,42,0.7);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 12px;
            margin-bottom: 8px;
        }
        .image-caption {
            font-size: 0.72rem;
            color: #64748B;
            text-align: center;
            margin-top: 8px;
            letter-spacing: 0.03em;
        }
        .gallery-label {
            font-size: 0.75rem;
            color: #38BDF8;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 700;
            margin-bottom: 12px;
            margin-top: 4px;
        }

        .footer-box {
            text-align: center;
            margin-top: 60px;
            padding: 24px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: #64748B;
            font-weight: 400;
            letter-spacing: 0.05em;
        }

        h3 {
            font-size: 1.2rem;
            text-transform: uppercase;
            font-weight: 800;
            margin-top: 0;
            padding-bottom: 16px;
            margin-bottom: 24px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            color: #F8FAFC;
            letter-spacing: 0.1em;
        }
        .panel-blue h3 {
            border-bottom: 2px solid rgba(8,47,73,0.15);
            color: #0C4A6E;
        }

        .layer-label {
            font-size: 0.8rem;
            color: #94A3B8;
            margin-top: 32px;
            display: block;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
        }
        .panel-blue .layer-label { color: #0369A1; }

        div[data-testid="stTextInput"] input {
            border-radius: 16px !important;
            padding: 16px 24px !important;
            font-size: 1.2rem !important;
            background-color: rgba(30,41,59,0.6) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: white !important;
            box-shadow: inset 0 2px 4px 0 rgba(0,0,0,0.2) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #38BDF8 !important;
            box-shadow: 0 0 0 2px rgba(56,189,248,0.3), inset 0 2px 4px 0 rgba(0,0,0,0.2) !important;
        }

        div[data-testid="stButton"] button {
            border-radius: 16px !important;
            font-weight: 800 !important;
            letter-spacing: 0.05em !important;
            min-height: 60px !important;
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(37,99,235,0.4) !important;
            transition: all 0.3s cubic-bezier(0.175,0.885,0.32,1.275) !important;
        }
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 15px rgba(37,99,235,0.6) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    ACCEPTED_TYPES = [
        "pdf",
        "png", "jpg", "jpeg", "tiff", "bmp", "webp",
        "mp4", "mov", "avi", "mkv", "webm",
    ]

    with st.sidebar:
        st.markdown("### 📁 Add to Corpus")
        st.caption("PDF · Images · Video")
        uploaded_files = st.file_uploader(
            "Upload files to the research corpus",
            type=ACCEPTED_TYPES,
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            st.write(f"{len(uploaded_files)} file(s) ready")
            if st.button("Process & Index", use_container_width=True):
                with st.spinner("Indexing — this may take a minute for videos…"):
                    try:
                        corpus_dir = os.path.join(workspace_dir, "data", "corpus")
                        os.makedirs(corpus_dir, exist_ok=True)
                        for uf in uploaded_files:
                            dest = os.path.join(corpus_dir, uf.name)
                            with open(dest, "wb") as fh:
                                fh.write(uf.getvalue())
                        from agent.ingest import initialize_vector_db
                        initialize_vector_db()
                        st.success("✅ Corpus updated")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        st.markdown("---")
        st.markdown("### 📊 Corpus Status")

        corpus_dir = os.path.join(workspace_dir, "data", "corpus")
        corpus_count = len(list(__import__("pathlib").Path(corpus_dir).glob("*.pdf"))) if os.path.isdir(corpus_dir) else 0
        st.caption(f"📂 Corpus PDFs: **{corpus_count}**")
        text_pts = _qdrant_text_count()
        st.caption(f"📝 Text chunks indexed: **{text_pts}**")
        try:
            from qdrant_client import QdrantClient
            img_pts = QdrantClient(url="http://localhost:6333").get_collection("heritage_lens_images").points_count
            st.caption(f"🖼️ Images indexed: **{img_pts}**")
        except Exception:
            pass
        video_pts = _qdrant_video_chunk_count()
        if video_pts > 0:
            st.caption(f"🎬 Video chunks indexed: **{video_pts}**")

        st.markdown("---")
        st.caption("Heritage Lens — Accountable AI for Specialised Research")

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="header-box">
        <h2>{UI_TITLE}</h2>
        <p>KXSB AR26 — Mission 4</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Search bar ───────────────────────────────────────────────────────────
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "Query",
            placeholder="[ Ask a research question in any language… ]",
            label_visibility="collapsed",
        )
    with col_btn:
        st.markdown("<div style='margin-top:2px'></div>", unsafe_allow_html=True)
        search_button = st.button("Search", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Lazy-load agent modules ──────────────────────────────────────────────
    import importlib
    import agent.image_extractor, agent.generator, agent.retriever, agent.pipeline
    importlib.reload(agent.image_extractor)
    importlib.reload(agent.generator)
    importlib.reload(agent.retriever)
    importlib.reload(agent.pipeline)
    from agent.pipeline import run_pipeline
    from agent.image_extractor import extract_images_for_keyword

    # ── Default panel content ────────────────────────────────────────────────
    ans_text          = "[Text block — grounded answer based on retrieved sources]"
    src_text          = "Submit a query to parse data sources…"
    transparency_text = "Submit a query to evaluate epistemic bounds…"
    # list of (image_path, source_name, page_number)
    image_results     = []
    video_chunks      = []

    # ── Run pipeline ─────────────────────────────────────────────────────────
    if search_button and query:
        with st.spinner("Heritage Lens is retrieving sources and building the transparency report…"):
            try:
                result = run_pipeline(query)

                ans_text = result.get("layer_1_answer", "Error in Layer 1").replace("\n", "<br>")
                src_text = result.get("layer_2_sources", "Error in Layer 2").replace("\n", "<br>")

                # ── Layer 3 rendering ────────────────────────────────────────
                trans_raw = result.get("layer_3_transparency", "Error in Layer 3").strip()
                for title in ["⚠️ SOURCE BIAS", "📄 ABSENCES", "🕵️ INTERPRETIVE LIMITS", "⚠️ CONFIDENCE"]:
                    trans_raw = (trans_raw
                        .replace(f"**{title}**", title)
                        .replace(f"### {title}", title)
                        .replace(f"## {title}", title))

                titles = {
                    "⚠️ SOURCE BIAS":        "#EF4444",
                    "📄 ABSENCES":            "#F59E0B",
                    "🕵️ INTERPRETIVE LIMITS": "#0EA5E9",
                    "⚠️ CONFIDENCE":          "#10B981",
                }

                parts, current_title, current_content = [], None, []
                for line in trans_raw.split("\n"):
                    found = next((t for t in titles if line.strip().startswith(t)), None)
                    if found:
                        if current_title:
                            parts.append((current_title, "\n".join(current_content).strip()))
                        elif "\n".join(current_content).strip():
                            parts.append((None, "\n".join(current_content).strip()))
                        current_title = found
                        current_content = [line[len(found):].strip()]
                    else:
                        current_content.append(line)
                if current_title:
                    parts.append((current_title, "\n".join(current_content).strip()))
                elif "\n".join(current_content).strip():
                    parts.append((None, "\n".join(current_content).strip()))

                rendered_html = ""
                for t, content in parts:
                    content_html = content.replace("\n", "<br>")
                    if t in titles:
                        c = titles[t]
                        rendered_html += (
                            f'<div style="border-left:3px solid {c};padding-left:12px;margin-bottom:20px;">'
                            f'<span style="color:{c};font-weight:800;font-size:0.85em;text-transform:uppercase;letter-spacing:0.05em;">{t}</span>'
                            f'<br><br><span style="color:rgba(255,255,255,0.85);font-size:0.95em;">{content_html}</span></div>'
                        )
                    elif content_html:
                        rendered_html += f"<p>{content_html}</p>"

                transparency_text = rendered_html or trans_raw.replace("\n", "<br>")

                # ── Video Evidence (timestamped chunks) ─────────────────────
                video_chunks = []
                for ch in result.get("retrieved_chunks", []):
                    meta = ch.get("metadata", {})
                    if meta.get("modality") in ("audio_transcript", "visual_caption", "ocr_text"):
                        video_chunks.append(ch)

                # ── Image retrieval (Qdrant semantic search, keyword fallback) ──
                qdrant_images = result.get("retrieved_images", [])
                if qdrant_images:
                    image_results = [
                        (hit["image_path"], hit["metadata"].get("source_name", ""), hit["metadata"].get("page_number", ""))
                        for hit in qdrant_images
                        if os.path.exists(hit["image_path"])
                    ]
                if not image_results:
                    keyword = result.get("layer_4_image_keyword")
                    retrieved_chunks = result.get("retrieved_chunks", [])
                    if keyword:
                        st.toast(f"Scanning corpus for visual data matching '{keyword}'…")
                        image_results = extract_images_for_keyword(keyword, retrieved_chunks, MAX_IMAGES)

            except Exception as e:
                ans_text = f"Internal Error: {str(e)}"

    # ── Video Evidence gallery ───────────────────────────────────────────────
    if video_chunks:
        st.markdown('<p class="gallery-label">🎬 Video Evidence</p>', unsafe_allow_html=True)
        vid_cols = st.columns(min(len(video_chunks), 3))
        for col, ch in zip(vid_cols, video_chunks[:3]):
            meta = ch.get("metadata", {})
            start = meta.get("start", 0)
            end = meta.get("end", 0)
            modality = meta.get("modality", "video")
            video_url = meta.get("video_url", "")
            source_name = meta.get("source_name", "")
            badge_color = {
                "audio_transcript": "#0EA5E9",
                "visual_caption": "#8B5CF6",
                "ocr_text": "#F59E0B",
            }.get(modality, "#64748B")
            seek_link = ""
            if video_url:
                # Generate a deep-link with timestamp if possible
                # For local files, we can't deep-link; for HTTP URLs, we can append #t= start
                if video_url.startswith("http"):
                    seek_link = f'<br><a href="{video_url}#t={int(start)}" target="_blank" style="color:#38BDF8;font-size:0.75rem;font-weight:700;">⏯ Seek to {start}s</a>'
            snippet = ch.get("text", "")[:120].replace("\n", " ")
            if len(ch.get("text", "")) > 120:
                snippet += "…"
            col.markdown(
                f'<div class="image-gallery-card">'
                f'<div style="font-size:0.75rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.05em;font-weight:700;margin-bottom:4px;">'
                f'{source_name}</div>'
                f'<div style="font-size:0.85rem;color:#E2E8F0;line-height:1.4;margin-bottom:8px;">{snippet}</div>'
                f'<div style="display:flex;gap:6px;align-items:center;">'
                f'<span style="background:{badge_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;text-transform:uppercase;">{modality}</span>'
                f'<span style="color:#64748B;font-size:0.72rem;">⏱ {start}s – {end}s</span>'
                f'</div>'
                f'{seek_link}'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Image gallery (shown only after a query returns images) ──────────────
    if image_results:
        st.markdown('<p class="gallery-label">Visual Evidence Retrieved from Corpus</p>', unsafe_allow_html=True)
        img_cols = st.columns(len(image_results))
        for col, (img_path, pdf_name, page_num) in zip(img_cols, image_results):
            if os.path.exists(img_path):
                b64 = img_to_b64(img_path)
                short_name = pdf_name[:40] + "…" if len(pdf_name) > 40 else pdf_name
                col.markdown(
                    f'<div class="image-gallery-card">'
                    f'<img src="data:image/png;base64,{b64}" style="width:100%;border-radius:8px;">'
                    f'<p class="image-caption">{short_name} · p.{page_num}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Three-panel results ───────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="panel">'
            f'<h3>The Answer</h3>'
            f'<div class="panel-content"><p>{ans_text}</p></div>'
            f'<span class="layer-label">Layer 1 — Direct answer. Only retrieved content. General knowledge labelled [BACKGROUND]</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="panel">'
            f'<h3>Sources</h3>'
            f'<div class="panel-content"><p>{src_text}</p></div>'
            f'<span class="layer-label">Layer 2 — Full attribution for every source used</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="panel-blue">'
            f'<h3>What the System Doesn\'t Know</h3>'
            f'<div class="panel-content">{transparency_text}</div>'
            f'<span class="layer-label">Layer 3 — Epistemic transparency, tied to retrieved data</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("""
    <div class="footer-box">
        Heritage Lens Multimodal Agent — Accountable AI for Specialised Research
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
