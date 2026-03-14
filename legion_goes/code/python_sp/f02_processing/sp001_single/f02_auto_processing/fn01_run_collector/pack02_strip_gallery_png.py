# =============================================================================
# Path: legion_goes/code/python_sp/f02_processing/sp001_single/f02_auto_processing/fn01_run_collector/pack02_strip_gallery_png.py
# Version: 1.1.0 (Dynamic Schema Sync)
# =============================================================================

from pathlib import Path
from PIL import Image
from typing import Dict, Any, Optional

# IMPORTACIÓN CENTRALIZADA
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single

# --- CONTRATO DE SALIDA (Fácilmente ampliable en el futuro) ---
dict_output_schema = {
    "gallery_strip": "gallery.png"
}

def pack02_strip_gallery_png(
    sat_id: str, 
    product_id: str, 
    year: int, 
    day: int, 
    s_timestamp_short: str, 
    fnp_tag: str
) -> Optional[Dict[str, Any]]:
    """
    Ensambla el 'BAG' para el proceso de generación de la tira de galería.
    Ahora incluye un esquema de salida para que el Auditor sepa qué buscar.
    """
    # 1. Resolver carpeta de salida
    str_output_folder_abs = get_folder_full_path_proc_single(
        sat_id=sat_id, product_id=product_id, year=year, day=day,
        s_timestamp_short=s_timestamp_short, fnp_tag=fnp_tag
    )

    if not str_output_folder_abs: 
        return None

    # 2. Generar rutas absolutas para la auditoría de la Action 01/02
    dict_output_file_path = {
        key: str(Path(str_output_folder_abs) / filename)
        for key, filename in dict_output_schema.items()
    }

    # 3. Retornar el BAG con el estándar del sistema
    return {
        "fnp_python_code": generate_fnp_preview_strip_gallery,
        "execution_kwargs": {
            "output_folder": str_output_folder_abs,
            "strip_filename": dict_output_schema["gallery_strip"], # Usamos el nombre del esquema
            "target_width": 600,
            "overwrite": False
        },
        "meta": {
            "task_name": "Gallery Strip Generation",
            "output_folder": str_output_folder_abs,
            "dict_output_file_name": dict_output_schema # Requerido por Action 01
        },
        "execution_kwargs_audit": dict_output_file_path # Mapeo directo de rutas para el JSON
    }

# =============================================================================
# CORE LOGIC (FNP)
# =============================================================================

def generate_fnp_preview_strip_gallery(
    output_folder: str, 
    strip_filename: str = "gallery.png", 
    target_width: int = 600, 
    overwrite: bool = False
) -> bool:
    """
    Busca todos los PNGs en la carpeta y los concatena horizontalmente.
    """
    folder = Path(output_folder)
    gallery_path = folder / strip_filename
    
    if gallery_path.exists() and not overwrite: 
        return True
        
    # Listar PNGs ignorando la propia galería si ya existe
    png_files = sorted([f for f in folder.glob("*.png") if f.name != strip_filename])
    
    if not png_files: 
        print(f"      ⚠️  [GALLERY] No PNG files found in {output_folder}")
        return False
        
    try:
        thumbs = []
        for f in png_files:
            with Image.open(f) as img:
                img = img.convert("RGBA")
                aspect_ratio = img.height / img.width
                new_size = (target_width, int(target_width * aspect_ratio))
                thumbs.append(img.resize(new_size, Image.Resampling.LANCZOS))
        
        # Calcular dimensiones del strip
        total_width = sum(t.width for t in thumbs)
        max_height = max(t.height for t in thumbs)
        
        # Crear lienzo transparente
        strip = Image.new("RGBA", (total_width, max_height), (255, 255, 255, 0))
        
        # Pegar imágenes
        current_x = 0
        for thumb in thumbs:
            strip.paste(thumb, (current_x, 0))
            current_x += thumb.width
            
        strip.save(gallery_path)
        print(f"      📸 [GALLERY] Created: {strip_filename}")
        return True
        
    except Exception as e:
        print(f"      ❌ [GALLERY ERROR] {e}")
        return False
