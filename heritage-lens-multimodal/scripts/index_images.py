#!/usr/bin/env python3
"""
Optional script to index images from PDFs
Can be run separately from main system without affecting text indexing
"""

import asyncio
import sys
import io
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path.home() / "heritage-lens-multimodal"))


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nTo enable image indexing, install:")
        print("  pip install PyMuPDF Pillow sentence-transformers qdrant-client")
        print("\nOr install all optional dependencies:")
        print("  pip install -r requirements-optional.txt")
        return False


async def extract_images_from_pdf(
    pdf_path: Path,
    min_size: tuple = (100, 100)
) -> List[Dict[str, Any]]:
    """
    Extract images from a PDF file

    Args:
        pdf_path: Path to PDF file
        min_size: Minimum image size (width, height) to include

    Returns:
        List of extracted image data dictionaries
    """
    import fitz  # PyMuPDF
    from PIL import Image

    images = []

    print(f"  Processing {pdf_path.name}...")

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    # Check minimum size
                    if pil_image.width < min_size[0] or pil_image.height < min_size[1]:
                        continue

                    # Generate unique ID
                    image_hash = hashlib.md5(image_bytes).hexdigest()
                    point_id = int(image_hash[:16], 16)  # Use first 16 chars as int

                    images.append({
                        "point_id": point_id,
                        "pil_image": pil_image,
                        "source": pdf_path.name,
                        "page": page_num + 1,
                        "image_index": img_index,
                        "width": pil_image.width,
                        "height": pil_image.height,
                        "format": image_ext,
                        "xref": xref
                    })

                except Exception as e:
                    print(f"    ⚠️  Error processing image {img_index} on page {page_num + 1}: {e}")

        doc.close()

    except Exception as e:
        print(f"  ❌ Error processing PDF: {e}")

    return images


async def index_images_to_qdrant(
    images: List[Dict[str, Any]],
    collection_name: str = "heritage_lens_images",
    qdrant_url: str = "http://localhost:6333"
) -> Dict[str, int]:
    """
    Index images to Qdrant vector store

    Args:
        images: List of image data dictionaries
        collection_name: Name of Qdrant collection
        qdrant_url: URL of Qdrant server

    Returns:
        Statistics dict with counts
    """
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance

    # Initialize services
    print("  Initializing CLIP model...")
    clip_model = SentenceTransformer('clip-ViT-B-32')

    print(f"  Connecting to Qdrant at {qdrant_url}...")
    qdrant = QdrantClient(url=qdrant_url)

    # Create image collection if not exists
    try:
        qdrant.get_collection(collection_name)
        print(f"  ✓ Collection '{collection_name}' exists")
    except Exception:
        print(f"  Creating collection '{collection_name}'...")
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=512,  # CLIP embedding size
                distance=Distance.COSINE
            )
        )
        print(f"  ✓ Collection created")

    # Index images
    indexed_count = 0
    skipped_count = 0
    batch_size = 10

    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        points = []

        for img_data in batch:
            try:
                # Generate embedding
                embedding = clip_model.encode(img_data["pil_image"])

                # Prepare metadata
                metadata = {
                    "source": img_data["source"],
                    "page": img_data["page"],
                    "image_index": img_data["image_index"],
                    "width": img_data["width"],
                    "height": img_data["height"],
                    "format": img_data["format"],
                    "xref": img_data["xref"]
                }

                # Create point
                points.append(PointStruct(
                    id=img_data["point_id"],
                    vector=embedding.tolist(),
                    payload=metadata
                ))

            except Exception as e:
                print(f"    ⚠️  Error encoding image: {e}")
                skipped_count += 1

        # Upload batch
        if points:
            try:
                qdrant.upsert(
                    collection_name=collection_name,
                    points=points
                )
                indexed_count += len(points)
                print(f"  Indexed {indexed_count}/{len(images)} images...")
            except Exception as e:
                print(f"    ⚠️  Error uploading batch: {e}")
                skipped_count += len(points)

    return {
        "indexed": indexed_count,
        "skipped": skipped_count,
        "total": len(images)
    }


async def main():
    """Main entry point for image indexing script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Index images from PDFs into Qdrant vector store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index all PDFs in default corpus directory
  python scripts/index_images.py

  # Index specific directory
  python scripts/index_images.py --pdf-dir /path/to/pdfs

  # Use custom Qdrant URL
  python scripts/index_images.py --qdrant-url http://qdrant:6333

  # Dry run - extract but don't index
  python scripts/index_images.py --dry-run
        """
    )

    parser.add_argument(
        "--pdf-dir",
        type=str,
        default=str(Path.home() / "heritage-lens-multimodal" / "data" / "corpus"),
        help="Directory containing PDF files (default: data/corpus)"
    )

    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant server URL (default: http://localhost:6333)"
    )

    parser.add_argument(
        "--collection",
        type=str,
        default="heritage_lens_images",
        help="Qdrant collection name (default: heritage_lens_images)"
    )

    parser.add_argument(
        "--min-size",
        type=int,
        nargs=2,
        default=[100, 100],
        metavar=("WIDTH", "HEIGHT"),
        help="Minimum image size to index (default: 100 100)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract images but don't index to Qdrant"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Heritage Lens - Image Indexing Script")
    print("=" * 70)
    print()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    pdf_dir = Path(args.pdf_dir)

    if not pdf_dir.exists():
        print(f"❌ Directory not found: {pdf_dir}")
        sys.exit(1)

    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF file(s) in {pdf_dir}")
    print()

    # Extract images from all PDFs
    all_images = []
    for pdf_path in pdf_files:
        images = await extract_images_from_pdf(pdf_path, tuple(args.min_size))
        all_images.extend(images)
        print(f"  Extracted {len(images)} images from {pdf_path.name}")

    print()
    print(f"Total images extracted: {len(all_images)}")

    if len(all_images) == 0:
        print("\n⚠️  No images found in PDFs")
        sys.exit(0)

    if args.dry_run:
        print("\n🔍 Dry run mode - images extracted but not indexed")
        print("   Run without --dry-run to index images")
        sys.exit(0)

    # Index images to Qdrant
    print()
    print("Indexing images to Qdrant...")
    stats = await index_images_to_qdrant(
        all_images,
        collection_name=args.collection,
        qdrant_url=args.qdrant_url
    )

    print()
    print("=" * 70)
    print("Indexing Complete")
    print("=" * 70)
    print(f"  Total images found:     {stats['total']}")
    print(f"  Successfully indexed:   {stats['indexed']}")
    print(f"  Skipped/Failed:         {stats['skipped']}")
    print()
    print(f"Images are now searchable via the Vision Agent!")
    print(f"Collection: {args.collection}")


if __name__ == "__main__":
    asyncio.run(main())
