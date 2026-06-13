import os
import uuid
from pathlib import Path
from agent.env_loader import load_env

load_env()

SIGLIP_MODEL = "google/siglip2-base-patch16-224"
IMAGE_CACHE_DIR = None  # set dynamically


def _embed_image(image_path: str, processor, model) -> list:
    import torch
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        outputs = model.vision_model(pixel_values=inputs["pixel_values"])
        features = outputs.pooler_output  # (1, 768)
        features = features / features.norm(dim=-1, keepdim=True)
    return features[0].cpu().numpy().tolist()


def index_images_from_corpus(corpus_dir: str, qdrant_client):
    from transformers import AutoProcessor, AutoModel
    from pypdf import PdfReader
    from PIL import Image
    import io
    from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType, PointStruct

    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(workspace_dir, "data", "cache", "images")
    os.makedirs(cache_dir, exist_ok=True)

    print("=== INITIALIZING QDRANT IMAGE COLLECTION ===")
    qdrant_client.delete_collection("heritage_lens_images")
    qdrant_client.create_collection(
        "heritage_lens_images",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
    qdrant_client.create_payload_index(
        "heritage_lens_images", "source_name", PayloadSchemaType.KEYWORD
    )
    qdrant_client.create_payload_index(
        "heritage_lens_images", "media_type", PayloadSchemaType.KEYWORD
    )
    qdrant_client.create_payload_index(
        "heritage_lens_images", "page_number", PayloadSchemaType.INTEGER
    )
    print("Loading SigLIP 2 model (downloads ~350MB on first run)...")
    from transformers import SiglipModel
    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL)
    model = SiglipModel.from_pretrained(SIGLIP_MODEL)
    model.eval()

    pdf_files = sorted(Path(corpus_dir).glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in corpus — skipping image indexing.")
        return

    points = []
    total_images = 0

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        pdf_stem = pdf_path.stem[:40].replace(" ", "_")
        print(f"Extracting images from '{pdf_name}'...")
        try:
            reader = PdfReader(str(pdf_path))
        except Exception as e:
            print(f"  Error reading {pdf_name}: {e}")
            continue

        for page_num, page in enumerate(reader.pages):
            if not page.images:
                continue
            img_idx = 0
            for image_obj in page.images:
                if len(image_obj.data) <= 10240:
                    continue
                try:
                    img = Image.open(io.BytesIO(image_obj.data)).convert("RGB")
                    save_path = os.path.join(
                        cache_dir, f"{pdf_stem}_p{page_num+1}_{img_idx}.png"
                    )
                    img.save(save_path)

                    vector = _embed_image(save_path, processor, model)
                    points.append(PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "source_name": pdf_name,
                            "page_number": page_num + 1,
                            "media_type": "pdf_image",
                            "image_path": save_path,
                        },
                    ))
                    img_idx += 1
                    total_images += 1

                    if len(points) >= 50:
                        qdrant_client.upsert("heritage_lens_images", points=points)
                        print(f"  Upserted batch of {len(points)} images.")
                        points = []
                except Exception as e:
                    print(f"  Error processing image on page {page_num+1}: {e}")

    if points:
        qdrant_client.upsert("heritage_lens_images", points=points)

    print(f"=== IMAGE INDEXING COMPLETE: {total_images} images from {len(pdf_files)} PDFs ===")


STANDALONE_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def index_standalone_images(corpus_dir: str, qdrant_client):
    """Embed image files uploaded directly (not extracted from PDFs) into heritage_lens_images."""
    import shutil
    from transformers import SiglipModel
    from qdrant_client.http.models import PointStruct

    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(workspace_dir, "data", "cache", "images")
    os.makedirs(cache_dir, exist_ok=True)

    image_files = [f for f in Path(corpus_dir).iterdir()
                   if f.suffix.lower() in STANDALONE_IMAGE_EXTS]
    if not image_files:
        return

    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL)
    model = SiglipModel.from_pretrained(SIGLIP_MODEL)
    model.eval()

    points = []
    for img_path in image_files:
        dest = os.path.join(cache_dir, img_path.name)
        if not os.path.exists(dest):
            shutil.copy2(str(img_path), dest)
        try:
            vector = _embed_image(dest, processor, model)
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "source_name": img_path.name,
                    "page_number": 0,
                    "media_type": "uploaded_image",
                    "image_path": dest,
                },
            ))
        except Exception as e:
            print(f"  Error embedding {img_path.name}: {e}")

    if points:
        qdrant_client.upsert("heritage_lens_images", points=points)
        print(f"Indexed {len(points)} standalone images.")


def index_video_frames(video_path: str, qdrant_client, fps: float = 1.0):
    """
    Index keyframes from a video file into heritage_lens_images.
    Requires ffmpeg-python: pip install ffmpeg-python
    Video frames are stored with media_type='video_frame'.
    """
    import ffmpeg
    from transformers import AutoProcessor, SiglipModel
    from PIL import Image
    import tempfile
    from qdrant_client.http.models import PointStruct

    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(workspace_dir, "data", "cache", "images")
    os.makedirs(cache_dir, exist_ok=True)

    video_id = Path(video_path).stem
    print(f"Extracting keyframes from '{video_id}' at {fps} fps...")

    processor = AutoProcessor.from_pretrained(SIGLIP_MODEL)
    model = SiglipModel.from_pretrained(SIGLIP_MODEL)
    model.eval()

    with tempfile.TemporaryDirectory() as tmpdir:
        frame_pattern = os.path.join(tmpdir, "frame_%04d.png")
        (
            ffmpeg.input(video_path)
            .filter("fps", fps=fps)
            .output(frame_pattern, vsync=0)
            .run(quiet=True)
        )
        frame_files = sorted(Path(tmpdir).glob("frame_*.png"))
        points = []
        for i, frame_path in enumerate(frame_files):
            timestamp_sec = round(i / fps)
            save_path = os.path.join(cache_dir, f"{video_id}_t{timestamp_sec}.png")
            Image.open(frame_path).save(save_path)
            vector = _embed_image(save_path, processor, model)
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "source_name": Path(video_path).name,
                    "video_id": video_id,
                    "timestamp_sec": timestamp_sec,
                    "media_type": "video_frame",
                    "image_path": save_path,
                },
            ))
            if len(points) >= 50:
                qdrant_client.upsert("heritage_lens_images", points=points)
                points = []

        if points:
            qdrant_client.upsert("heritage_lens_images", points=points)

    print(f"Indexed {len(frame_files)} frames from '{video_id}'.")
