"""
Path: src/legion_goes/task/task03_proc_single/actions/fnp/ABI_L2_MCMIPF_SP_single_fnp02/fn01_python_code.py
Version: 1.8.5
Description: FNP02 - Procesamiento de Infrarrojo Colorizado (Colorized IR) con transparencia.
"""

import os
import time
import gc
import json
import inspect
import warnings
import logging
import matplotlib
matplotlib.use('Agg') # Backend para servidores
import numpy as np
from PIL import Image
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

# --- Supresión de Logs innecesarios ---
warnings.filterwarnings("ignore")
logging.getLogger("satpy").setLevel(logging.ERROR)
logging.getLogger("pyresample").setLevel(logging.ERROR)

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS
# =============================================================================
dict_output_schema = {
    "png_CRSnative_ir": "CRS-GoesEast_IR_Colorized.png",
    "png_CRSnative_ir_transparent": "CRS-GoesEast_IR_Colorized_Transparent.png",
    "png_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.png",
    "png_CRSwgs84_ir_transparent": "CRS-WGS84_IR_Colorized_Transparent.png",
    "tif_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.tif",
    "json_meta": "meta.json",
    "gallery": "gallery.png"
}

# =============================================================================
# 2. UTILIDADES INTERNAS
# =============================================================================

def apply_grayscale_transparency(input_path, output_path, saturation_threshold=20):
    """Convierte pixeles grises (nubes) en transparentes para overlays."""
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)

def verify_fnp_interface(config_dict, fnp_function):
    sig = inspect.signature(fnp_function)
    fnp_expected_outputs = [p for p in sig.parameters.keys() if p not in ['nc_path', 'overwrite']]
    dict_keys = [k for k in config_dict.keys() if k != 'gallery']
    missing = [p for p in fnp_expected_outputs if p not in dict_keys]
    extra = [k for k in dict_keys if k not in fnp_expected_outputs]
    if not missing and not extra:
        return True, "✅ Interfaz sincronizada."
    return False, f"❌ Error de Interfaz: Faltan {missing}, Sobran {extra}"

# =============================================================================
# 3. FUNCIÓN DE PROCESAMIENTO
# =============================================================================

def fnp_python_code(
    nc_path, png_CRSnative_ir, png_CRSnative_ir_transparent,
    png_CRSwgs84_ir, png_CRSwgs84_ir_transparent,
    tif_CRSwgs84_ir, json_meta
):
    start_time = time.time()
    try:
        Path(png_CRSnative_ir).parent.mkdir(parents=True, exist_ok=True)

        # Step 01: Load
        print(f"      [Step 01/10] 🛰️  Loading IR Product...", end=" ", flush=True)
        scn = Scene(filenames=[str(nc_path)], reader='abi_l2_nc')
        product_id = 'colorized_ir_clouds'
        scn.load([product_id])
        print("Done.")

        # Step 02/03: Native IR & Transparency
        print(f"      [Step 02/10] 🖼️  Saving Native IR...", end=" ", flush=True)
        scn.save_datasets(writer='simple_image', datasets=[product_id], filename=str(png_CRSnative_ir))
        print("Done.")
        
        print(f"      [Step 03/10] 🎭  Applying Transparency (Native)...", end=" ", flush=True)
        apply_grayscale_transparency(png_CRSnative_ir, png_CRSnative_ir_transparent)
        print("Done.")

        # Step 05/06: Resample
        print(f"      [Step 05/10] 🗺️  Defining WGS84 Area...", end=" ", flush=True)
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        print("Done.")
        
        print(f"      [Step 06/10] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def)
        print("Done.")

        # Step 07/08: Save WGS84 & Transparency
        print(f"      [Step 07/10] 💾  Saving WGS84 PNG and GeoTIFF...", end=" ", flush=True)
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], filename=str(png_CRSwgs84_ir))
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], filename=str(tif_CRSwgs84_ir))
        print("Done.")

        print(f"      [Step 08/10] 🎭  Applying Transparency (WGS84)...", end=" ", flush=True)
        apply_grayscale_transparency(png_CRSwgs84_ir, png_CRSwgs84_ir_transparent)
        print("Done.")

        # Step 09: Metadata
        print(f"      [Step 09/10] 📝  Generating Metadata...", end=" ", flush=True)
        duration = round(time.time() - start_time, 2)
        if json_meta:
            with open(json_meta, 'w') as f:
                json.dump({
                    "source": Path(nc_path).name,
                    "duration_sec": duration,
                    "product": "COLORIZED_IR_CLOUDS",
                    "timestamp": datetime.now().isoformat()
                }, f, indent=4)
        print("Done.")

        # Step 10: Cleanup
        print(f"      [Step 10/10] 🧹  Cleaning memory...", end=" ", flush=True)
        del scn; del scn_res; gc.collect()
        print(f"Done. (Total time: {duration}s)")
        
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP02 ERROR] {str(e)}")
        return False

# Auto-verificación
status, report = verify_fnp_interface(dict_output_schema, fnp_python_code)
if not status: print(report)
