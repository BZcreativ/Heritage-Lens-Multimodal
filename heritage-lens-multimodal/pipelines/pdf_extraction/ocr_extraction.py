"""
OCR Extraction for image-based PDFs
"""

import io
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from PIL import Image


async def extract_pdf_with_ocr(
    pdf_file: Path,
    extracted_images_dir: Path,
    metadata: Dict = None,
    enrich_metadata_func=None,
    metadata_config: Dict = None
) -> Dict[str, Any]:
    """Extract text from PDF using OCR for image-based PDFs"""
    import fitz
    import pytesseract

    text_chunks = []
    images_extracted = []
    errors = []

    base_metadata = metadata or {}
    base_metadata.update({
        "source": pdf_file.name,
        "processed_at": datetime.now().isoformat(),
        "extraction_method": "ocr"
    })

    if metadata_config and metadata_config.get("enrich", True) and enrich_metadata_func:
        base_metadata = enrich_metadata_func(base_metadata, pdf_file.name)

    doc = fitz.open(pdf_file)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_number = page_num + 1

        # Render page to image at 2x scale for better OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # OCR the page
        try:
            text = pytesseract.image_to_string(img)
            if text.strip():
                chunk_metadata = base_metadata.copy()
                chunk_metadata["page"] = page_number
                chunk_metadata["chunk_type"] = "text"
                chunk_metadata["ocr"] = True

                text_chunks.append({
                    "content": text,
                    "metadata": chunk_metadata
                })
        except Exception as e:
            errors.append(f"OCR failed on page {page_number}: {str(e)}")

        # Save page image
        image_filename = f"{pdf_file.stem}_p{page_number}_ocr.png"
        image_path = extracted_images_dir / image_filename
        img.save(str(image_path))

        img_metadata = base_metadata.copy()
        img_metadata.update({
            "page": page_number,
            "width": img.width,
            "height": img.height,
            "extracted_from": str(pdf_file),
            "ocr_source": True
        })

        images_extracted.append({
            "path": str(image_path),
            "metadata": img_metadata
        })

    total_pages = len(doc)
    doc.close()

    return {
        "text_chunks": text_chunks,
        "images_extracted": images_extracted,
        "errors": errors,
        "total_pages": total_pages,
        "text_chunks_count": len(text_chunks),
        "images_count": len(images_extracted)
    }
