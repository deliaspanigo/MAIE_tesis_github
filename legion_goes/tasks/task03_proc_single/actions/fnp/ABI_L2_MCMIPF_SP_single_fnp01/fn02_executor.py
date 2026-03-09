"""
Path: src/legion_goes/task/task03_proc_single/actions/fnp/ABI_L2_MCMIPF_SP_single_fnp01/fn02_executor.py
Version: 1.8.5
Description: Executor for FNP01 - Orchestrates processing, verification, and gallery generation.
"""

import os
from pathlib import Path
from PIL import Image

# Importamos la lógica de fn01
from .fn01_python_code import run_fnp_python_code

def check_fnp_outputs_exist(dict_output):
    """
    Checks if all files defined in the dictionary exist on disk.
    """
    missing_files = []
    for key, file_path in dict_output.items():
        if not Path(file_path).exists():
            missing_files.append(str(file_path))
            
    is_complete = len(missing_files) == 0
    return is_complete

def generate_fnp_preview_strip(output_folder, strip_filename="gallery.png"):
    """
    Genera una tira horizontal (600px de ancho base) para previsualización rápida.
    """
    folder = Path(output_folder)
    png_files = sorted([f for f in folder.glob("*.png") if f.name != strip_filename])
    
    if not png_files:
        print(f"      ⚠️  No PNG files found to generate strip.")
        return False

    target_width = 600 
    thumbs = []
    
    try:
        for f in png_files:
            with Image.open(f) as img:
                img = img.convert("RGBA")
                aspect_ratio = img.height / img.width
                target_height = int(target_width * aspect_ratio)
                img_thumb = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                thumbs.append(img_thumb)

        total_width = sum(t.width for t in thumbs)
        max_height = max(t.height for t in thumbs)
        strip = Image.new("RGBA", (total_width, max_height), (255, 255, 255, 0))

        current_x = 0
        for thumb in thumbs:
            strip.paste(thumb, (current_x, 0))
            current_x += thumb.width

        strip.save(folder / strip_filename)
        print(f"      ✅ Preview strip generated: {strip_filename}")
        return True
    except Exception as e:
        print(f"      ❌ Error generating strip: {e}")
        return False

def run_executor(nc_path, dict_output, overwrite):
    """
    Main executor flow: Check -> Process (if needed) -> Gallery
    """
    # 1. Check if processing is already done
    # Nota: dict_output viene del Plan JSON procesado por Action 03
    all_done = check_fnp_outputs_exist(dict_output)
    
    if not all_done or overwrite:
        print(f"    🚀 [fnp01] Starting Processing: {Path(nc_path).name}")
        
        # 2. Execute the heavy python code from fn01
        # Mapeo EXPLÍCITO de llaves del diccionario a argumentos de fn01
        success = run_fnp_python_code(
            nc_path = nc_path,
            png_CRSnative_true_color = str(dict_output["png_CRSnative_true_color"]),
            png_CRSnative_true_color_day_only = str(dict_output["png_CRSnative_true_color_day_only"]),
            png_CRSwgs84_true_color = str(dict_output["png_CRSwgs84_true_color"]),
            png_CRSwgs84_true_color_day_only = str(dict_output["png_CRSwgs84_true_color_day_only"]),
            tif_CRSwgs84_true_color = str(dict_output["tif_CRSwgs84_true_color"]),
            json_meta = str(dict_output["json_meta"])
        )
        
        if success:
            # 3. Handle Gallery Generation
            # El path de gallery se extrae explícitamente del diccionario
            gallery_path = Path(dict_output["gallery"])
            
            generate_fnp_preview_strip(
                output_folder = gallery_path.parent, 
                strip_filename = gallery_path.name
            )
            return True
        else:
            return False
    else:
        print(f"    ✨ [fnp01] [SKIP] All outputs exist.")
        return True
