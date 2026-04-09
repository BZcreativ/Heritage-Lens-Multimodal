"""
Heritage Lens Multimodal UI - Gradio Version
Alternative web interface using Gradio for cultural heritage exploration
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project to path
sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

import gradio as gr
from PIL import Image

from agents.orchestrator import EnhancedOrchestrator

# Global orchestrator instance
_orchestrator = None

def get_orchestrator():
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedOrchestrator()
    return _orchestrator


async def process_query_gradio(
    query: str,
    top_k_text: int,
    top_k_images: int,
    show_layers: bool
) -> tuple:
    """
    Process a query and return formatted results for Gradio

    Returns:
        tuple: (answer, images, sources, epistemic, stats)
    """
    try:
        orchestrator = get_orchestrator()

        result = await orchestrator.process_query(
            query=query,
            top_k_text=top_k_text,
            top_k_images=top_k_images
        )

        # Layer 1: Answer
        answer = result["layers"]["l1_answer"]

        # Images
        images = []
        for img in result["retrieval"]["images"]:
            try:
                img_path = img.get("path", "")
                if Path(img_path).exists():
                    pil_img = Image.open(img_path)
                    caption = img.get("caption", "No caption")
                    similarity = img.get("similarity", 0)
                    images.append((pil_img, f"{caption}\n(Similarity: {similarity:.2f})"))
            except Exception as e:
                print(f"Error loading image {img.get('path')}: {e}")

        # Layer 2: Sources
        l2 = result["layers"]["l2_attribution"]
        sources_text = "## Text Sources\n\n"
        for src in l2.get("text_sources", []):
            ref = src.get("reference", "")
            source = src.get("source", "unknown")
            page = src.get("page")
            page_str = f", p.{page}" if page else ""
            sources_text += f"- {ref} {source}{page_str}\n"

        sources_text += "\n## Image Sources\n\n"
        for img in l2.get("image_sources", []):
            ref = img.get("reference", "")
            caption = img.get("caption", "Image")
            sources_text += f"- {ref} {caption}\n"

        # Layer 3: Epistemic
        l3 = result["layers"]["l3_epistemic"]
        epistemic_text = ""
        if l3.get("textual_analysis"):
            epistemic_text += f"### Textual Analysis\n\n{l3['textual_analysis']}\n\n"
        if l3.get("visual_analysis"):
            epistemic_text += f"### Visual Analysis\n\n{l3['visual_analysis']}\n\n"
        if l3.get("overall_assessment"):
            epistemic_text += f"### Overall Assessment\n\n{l3['overall_assessment']}"

        # Stats
        stats = f"""## Processing Statistics

- **Processing Time**: {result['processing_time']:.2f}s
- **Revisions**: {result['revisions']}
- **Text Chunks Retrieved**: {result['retrieval']['stats']['text_retrieved']}
- **Images Retrieved**: {result['retrieval']['stats']['images_retrieved']}
- **Verdict**: {result['critique']['verdict']}
- **Confidence**: {result['critique'].get('confidence', 'N/A')}
- **Multimodal Coherence**: {result['critique'].get('multimodal_coherence', 'N/A')}
"""

        if not show_layers:
            sources_text = ""
            epistemic_text = ""

        return answer, images, sources_text, epistemic_text, stats

    except Exception as e:
        return f"Error: {str(e)}", [], "", "", ""


def process_query_sync(
    query: str,
    top_k_text: int,
    top_k_images: int,
    show_layers: bool
) -> tuple:
    """Synchronous wrapper for async function"""
    return asyncio.run(process_query_gradio(query, top_k_text, top_k_images, show_layers))


def create_ui() -> gr.Blocks:
    """Create the Gradio UI"""

    with gr.Blocks(title="Heritage Lens Multimodal", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🏛️ Heritage Lens Multimodal

        Explore cultural heritage through AI-powered multimodal analysis.
        Ask questions about artifacts, sites, and civilizations with integrated text and image retrieval.
        """)

        with gr.Row():
            with gr.Column(scale=2):
                # Query input
                query_input = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., What are Olmec colossal heads and what do they represent?",
                    lines=2
                )

                with gr.Row():
                    top_k_text = gr.Slider(1, 10, value=5, step=1, label="Text Chunks")
                    top_k_images = gr.Slider(1, 5, value=3, step=1, label="Images")

                show_layers = gr.Checkbox(
                    label="Show All Layers (Attribution & Epistemic)",
                    value=True
                )

                submit_btn = gr.Button("🔍 Search", variant="primary")

            with gr.Column(scale=3):
                # Answer output
                answer_output = gr.Markdown(label="Answer")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📸 Related Images")
                gallery_output = gr.Gallery(
                    label="Retrieved Images",
                    columns=3,
                    rows=1,
                    height="auto"
                )

        with gr.Row():
            with gr.Column():
                sources_output = gr.Markdown(label="Layer 2: Source Attribution")
            with gr.Column():
                epistemic_output = gr.Markdown(label="Layer 3: Epistemic Transparency")

        with gr.Row():
            stats_output = gr.Markdown(label="Statistics")

        # Event handlers
        submit_btn.click(
            fn=process_query_sync,
            inputs=[query_input, top_k_text, top_k_images, show_layers],
            outputs=[answer_output, gallery_output, sources_output, epistemic_output, stats_output]
        )

        # Example queries
        gr.Markdown("""
        ### Example Queries

        Try these example queries to explore the system:
        """)

        example_queries = [
            "What are Olmec colossal heads and what do they represent?",
            "Show me examples of Maya hieroglyphic writing",
            "Describe Aztec temple architecture",
            "What artifacts have been found at Teotihuacan?",
            "Compare Olmec and Maya artistic styles"
        ]

        for i, example in enumerate(example_queries, 1):
            gr.Button(f"Example {i}: {example[:50]}...", size="sm").click(
                fn=lambda e=example: (e,) + process_query_sync(e, 5, 3, True),
                inputs=[],
                outputs=[query_input, answer_output, gallery_output, sources_output, epistemic_output, stats_output]
            )

        gr.Markdown("""
        ---

        **Note:** This system retrieves information from indexed documents and images.
        For best results, ensure your cultural heritage corpus has been ingested.
        """)

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
