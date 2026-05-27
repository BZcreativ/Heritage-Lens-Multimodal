import os
import json
from pathlib import Path
try:
    from pypdf import PdfReader
except ImportError:
    print("WARNING: pypdf not installed.")

def load_or_build_cache(workspace_dir: str, assets_dir: str) -> dict:
    cache_path = os.path.join(assets_dir, "pdf_page_cache.json")
    
    # Find all PDFs in workspace
    pdf_files = {}
    for filepath in Path(workspace_dir).glob("*.pdf"):
        stat = filepath.stat()
        pdf_files[filepath.name] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime
        }
        
    # Check if cache exists and matches current PDFs
    use_cache = False
    cache_data = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            cached_files = cache_data.get("metadata", {}).get("pdf_files", {})
            
            # Verify if keys and their size/mtime match
            if set(pdf_files.keys()) == set(cached_files.keys()):
                match = True
                for name, info in pdf_files.items():
                    cached_info = cached_files[name]
                    if cached_info.get("size") != info["size"] or cached_info.get("mtime") != info["mtime"]:
                        match = False
                        break
                if match:
                    use_cache = True
        except Exception as e:
            print(f"Error reading cache: {e}")
            
    if use_cache:
        print("Using cached PDF page texts for image extraction.")
        return cache_data
        
    print("Building PDF page cache for image extraction (this happens only once or when PDFs change)...")
    cache_pages = []
    
    for filename, info in pdf_files.items():
        filepath = os.path.join(workspace_dir, filename)
        try:
            reader = PdfReader(filepath)
            for page_num, page in enumerate(reader.pages):
                # Only check pages that actually have images
                if len(page.images) > 0:
                    # Check if there is any image larger than 10KB
                    has_large_image = False
                    for image_obj in page.images:
                        if len(image_obj.data) > 10240:
                            has_large_image = True
                            break
                            
                    if has_large_image:
                        text = page.extract_text() or ""
                        cache_pages.append({
                            "pdf": filename,
                            "page_num": page_num,
                            "text": text
                        })
        except Exception as e:
            print(f"Error caching {filename}: {e}")
            
    cache_data = {
        "metadata": {
            "pdf_files": pdf_files
        },
        "pages": cache_pages
    }
    
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"Saved PDF page cache to {cache_path}")
    except Exception as e:
        print(f"Error saving cache: {e}")
        
    return cache_data

def extract_image_for_keyword(keyword: str) -> str:
    """
    Scans internal PDFs for the specified keyword using a pre-built cache. 
    If a page contains the keyword AND an image > 10KB, it extracts the first image 
    and saves it to the ui/assets folder, returning the relative path.
    Returns None if no image is found.
    """
    if not keyword or len(keyword.strip()) < 3:
        return None
        
    keyword = keyword.lower().strip()
    
    # Setup paths
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(workspace_dir, "ui", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Path to save the extracted image
    # Always overwrite the same file to save space
    save_path = os.path.join(assets_dir, "extracted_context_image.png")
    
    # Load cache
    cache_data = load_or_build_cache(workspace_dir, assets_dir)
    pages = cache_data.get("pages", [])
    
    # Find matching page
    for page_data in pages:
        text = page_data["text"]
        if keyword in text.lower():
            pdf_name = page_data["pdf"]
            page_num = page_data["page_num"]
            filepath = os.path.join(workspace_dir, pdf_name)
            
            try:
                reader = PdfReader(filepath)
                page = reader.pages[page_num]
                for image_obj in page.images:
                    if len(image_obj.data) > 10240:
                        # Extract and save
                        with open(save_path, "wb") as f:
                            f.write(image_obj.data)
                        
                        print(f"Extracted image from {pdf_name} page {page_num} for keyword '{keyword}'")
                        return save_path
            except Exception as e:
                print(f"Error extracting image from {pdf_name} page {page_num}: {e}")
                
    # No image found containing the keyword
    return None

if __name__ == "__main__":
    # Internal test
    res = extract_image_for_keyword("ossidiana")
    print(f"Result: {res}")
