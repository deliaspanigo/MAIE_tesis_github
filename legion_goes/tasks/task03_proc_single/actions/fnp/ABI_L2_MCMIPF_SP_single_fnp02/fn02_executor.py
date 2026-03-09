"""
Path: src/legion_goes/task/task03_proc_single/actions/fnp/ABI_L2_MCMIPF_SP_single_fnp02/fn02_executor.py
Version: 1.8.5
"""

import os
from pathlib import Path
from PIL import Image
from .fn01_python_code import run_fnp_python_code

def check_fnp_outputs_exist(dict_output):
    for key, file_path in dict_output.items():
        if not Path(file_path).exists():
            return False
    return True

def generate_fnp_preview_strip(output_folder, strip_filename="gallery.png"):
    folder = Path(output_folder)
    png_files = sorted([f for f in folder.glob("*.png") if f.name != strip_filename])
    if not png_files: return False

    target_width = 600 # 6 pulgadas
    thumbs = []
    try:
        for f in png_files:
            with Image.open(f) as img:
                img = img.convert("RGBA")
                aspect = img.height / img.width
                img_thumb = img.resize((target_width, int(target_width * aspect)), Image.Resampling.LANCZOS)
                thumbs.append(img_thumb)

        strip = Image.new("RGBA", (sum(t.width for t in thumbs), max(t.height for t in thumbs)), (255, 255, 255, 0))
        x = 0
        for t in thumbs:
            strip.paste(t, (x, 0))
            x += t.width
        strip.save(folder / strip_filename)
        print(f"      ✅ Preview strip (6'') generated: {strip_filename}")
        return True
    except Exception as e:
        print(f"      ❌ Gallery error: {e}"); return False

def run_executor(nc_path, dict_output, overwrite):
    if not overwrite and check_fnp_outputs_exist(dict_output):
        print(f"✨ [SKIP] FNP02 outputs already exist.")
        return True

    print(f"🚀 Starting FNP02 (Colorized IR)...")
    success = run_fnp_python_code(
        nc_path = str(nc_path),
        png_CRSnative_ir = str(dict_output["png_CRSnative_ir"]),
        png_CRSnative_ir_transparent = str(dict_output["png_CRSnative_ir_transparent"]),
        png_CRSwgs84_ir = str(dict_output["png_CRSwgs84_ir"]),
        png_CRSwgs84_ir_transparent = str(dict_output["png_CRSwgs84_ir_transparent"]),
        tif_CRSwgs84_ir = str(dict_output["tif_CRSwgs84_ir"]),
        json_meta = str(dict_output["json_meta"])
    )

    if success:
        gal = Path(dict_output["gallery"])
        generate_fnp_preview_strip(gal.parent, gal.name)
        return True
    return False
