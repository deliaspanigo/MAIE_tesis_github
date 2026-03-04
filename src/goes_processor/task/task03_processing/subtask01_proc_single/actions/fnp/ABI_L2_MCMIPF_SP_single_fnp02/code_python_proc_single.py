"""
Path: src/goes_processor/task/task03_processing/subtask01_proc_single/actions/fnp/ABI_L2_MCMIPF_SP_single_fnp02/code_python_proc_single.py
Version: 1.5.0
Description: Versión Genérica. Procesamiento de Infrarrojo Colorizado (Colorized IR) 
             con transparencia para el producto MCMIPF.
"""

import os
import time
import gc
import json
import inspect
import warnings
import logging
import matplotlib
# Configuración de backend no interactivo para servidores (Legion)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

# --- Supresión de Warnings de Satpy/HDF5 ---
warnings.filterwarnings("ignore")
logging.getLogger("satpy").setLevel(logging.ERROR)

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS (Genérico)
# =============================================================================
dict_output_schema = {
    "png_CRSnative_ir": "CRS-GoesEast_IR_Colorized.png",
    "png_CRSnative_ir_transparent": "CRS-GoesEast_IR_Colorized_Transparent.png",
    "png_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.png",
    "png_CRSwgs84_ir_transparent": "CRS-WGS84_IR_Colorized_Transparent.png",
    "tif_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.tif",
    "json_meta": "meta.json"
}

# =============================================================================
# 2. UTILIDADES INTERNAS (Transparencia y Verificación)
# =============================================================================

def verify_fnp_interface(config_dict: dict, fnp_function):
    """Verifica la sincronía entre el diccionario de nombres y los argumentos."""
    sig = inspect.signature(fnp_function)
    fnp_expected_outputs = [p for p in sig.parameters.keys() if p not in ['nc_path', 'overwrite']]
    dict_keys = list(config_dict.keys())
    missing = [p for p in fnp_expected_outputs if p not in dict_keys]
    extra = [k for k in dict_keys if k not in fnp_expected_outputs]
    if not missing and not extra:
        return True, "✅ Interfaz sincronizada."
    else:
        return False, f"❌ Error de Interfaz: Faltan {missing}, Sobran {extra}"

def apply_grayscale_transparency(input_path: Path, output_path: Path, saturation_threshold=20):
    """Convierte pixeles grises (nubes) en transparentes para overlays."""
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    # Diferencia entre canales (baja diferencia = gris)
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)

# =============================================================================
# 3. FUNCIÓN DE PROCESAMIENTO (Nombre Genérico)
# =============================================================================

def execute_fnp_processing(
    nc_path: str,
    png_CRSnative_ir: str,
    png_CRSnative_ir_transparent: str,
    png_CRSwgs84_ir: str,
    png_CRSwgs84_ir_transparent: str,
    tif_CRSwgs84_ir: str,
    json_meta: str,
    overwrite: bool = False
):
    """Generación de IR Colorized Clouds con argumentos explícitos."""
    start_ts = time.time()
    
    if not overwrite and Path(png_CRSnative_ir_transparent).exists():
        return True

    try:
        # Asegurar directorios
        Path(png_CRSnative_ir).parent.mkdir(parents=True, exist_ok=True)

        # 1. Carga de Escena
        scn = Scene(filenames=[str(nc_path)], reader='abi_l2_nc', reader_kwargs={'engine': 'h5netcdf'})
        product_id = 'colorized_ir_clouds'
        scn.load([product_id])

        # 2. Guardado Nativo y Transparencia
        scn.save_datasets(writer='simple_image', datasets=[product_id], filename=png_CRSnative_ir)
        apply_grayscale_transparency(Path(png_CRSnative_ir), Path(png_CRSnative_ir_transparent))

        # 3. Reproyección WGS84
        area_def = AreaDefinition(
            'global_wgs84', 'Lat-Lon Global', 'wgs84', 
            {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}, 
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        path_cache = satpy_config.get("cache_dir")
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # 4. Exportación WGS84 y GeoTIFF
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], filename=png_CRSwgs84_ir)
        apply_grayscale_transparency(Path(png_CRSwgs84_ir), Path(png_CRSwgs84_ir_transparent))
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], filename=tif_CRSwgs84_ir)

        # 5. Metadata
        duration = round((time.time() - start_ts), 2)
        if json_meta:
            with open(json_meta, 'w') as f:
                json.dump({
                    "source": Path(nc_path).name,
                    "duration_sec": duration,
                    "product": "COLORIZED_IR_CLOUDS",
                    "timestamp": datetime.now().isoformat()
                }, f, indent=4)

        # Limpieza
        del scn; del scn_res; gc.collect()
        return True

    except Exception as e:
        print(f"❌ [FNP02 ERROR] {str(e)}")
        return False

# =============================================================================
# 4. AUTO-VERIFICACIÓN AL IMPORTAR
# =============================================================================
status, report = verify_fnp_interface(dict_output_schema, execute_fnp_processing)
if not status:
    print(f"⚠️ Advertencia de consistencia en FNP02: {report}")
