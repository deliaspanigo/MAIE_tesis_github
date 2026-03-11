"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/generate_fnp_preview_strip_gallery.py
Version: 1.1.0
Description: Utility to generate a horizontal preview strip (gallery) from PNG files.
"""

from pathlib import Path
from PIL import Image

def generate_fnp_preview_strip_gallery(output_folder: str, strip_filename: str = "gallery.png", 
                                       target_width: int = 600, overwrite: bool = False) -> bool:
    """
    Creates a horizontal montage of all PNG files found in a directory.
    
    Args:
        output_folder (str): Path to the folder containing PNGs.
        strip_filename (str): Name of the output gallery file.
        target_width (int): Fixed width for each thumbnail (maintains aspect ratio).
        overwrite (bool): If False and gallery exists, skips generation.
        
    Returns:
        bool: True if generated successfully or skipped, False if failed.
    """
    folder = Path(output_folder)
    gallery_path = folder / strip_filename

    # --- 1. OVERWRITE CHECK ---
    if gallery_path.exists() and not overwrite:
        print(f"      ✨ [SKIP] Gallery already exists: {strip_filename}")
        return True

    # --- 2. FILE GATHERING ---
    # Find all PNGs except the gallery itself
    png_files = sorted([f for f in folder.glob("*.png") if f.name != strip_filename])
    
    if not png_files:
        print(f"      ⚠️ [GALLERY] No PNG files found in {folder.name}")
        return False

    try:
        thumbs = []
        for f in png_files:
            # Use 'with' to ensure the file is closed immediately after processing
            with Image.open(f) as img:
                img = img.convert("RGBA")
                aspect_ratio = img.height / img.width
                new_size = (target_width, int(target_width * aspect_ratio))
                
                # Create a copy in memory before the 'with' block closes
                thumbs.append(img.resize(new_size, Image.Resampling.LANCZOS))
        
        # --- 3. CANVAS ASSEMBLY ---
        total_width = sum(t.width for t in thumbs)
        max_height = max(t.height for t in thumbs)
        
        # Create a transparent background
        strip = Image.new("RGBA", (total_width, max_height), (255, 255, 255, 0))
        
        current_x = 0
        for thumb in thumbs:
            strip.paste(thumb, (current_x, 0))
            current_x += thumb.width
            
        # --- 4. SAVE ---
        strip.save(gallery_path)
        print(f"      📸 [GALLERY] Created successfully: {strip_filename}")
        return True

    except Exception as e:
        print(f"      ❌ [GALLERY ERROR] Failed to generate strip: {e}")
        return False
