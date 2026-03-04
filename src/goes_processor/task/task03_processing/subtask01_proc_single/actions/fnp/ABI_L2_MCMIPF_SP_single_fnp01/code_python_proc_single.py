"""
Path: src/goes_processor/task/task03_processing/subtask01_proc_single/actions/fnp/ABI_L2_MCMIPF_SP_single_fnp01/code_python_proc_single.py
Version: 1.5.0
Description: Versión Genérica. Definición de diccionarios de salida y 
             función de procesamiento Satpy para MCMIPF.
"""

import os
import time
import gc
import json
import inspect
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition

# =============================================================================
# 1. DICCIONARIO DE DEFINICIÓN DE SALIDAS (Contrato de Nombres)
# =============================================================================
# Se mantiene genérico: 'dict_output_schema'
dict_output_schema = {
    "png_CRSnative_true_color": "CRS-GoesEast_TrueColor.png",
    "png_CRSnative_true_color_day_only": "CRS-GoesEast_TrueColor_DayOnly.png",
    "png_CRSwgs84_true_color": "CRS-WGS84_TrueColor.png",
    "png_CRSwgs84_true_color_day_only": "CRS-WGS84_TrueColor_DayOnly.png",
    "tif_CRSwgs84_true_color": "CRS-WGS84_TrueColor.tif",
    "json_meta": "meta.json"
}

# =============================================================================
# 2. AUDITORÍA DE INTERFAZ (Genérica)
# =============================================================================

def verify_fnp_interface(config_dict: dict, fnp_function):
    """
    Verifica que las llaves del diccionario coincidan con los argumentos.
    """
    sig = inspect.signature(fnp_function)
    fnp_expected_outputs = [p for p in sig.parameters.keys() if p not in ['nc_path', 'overwrite']]
    dict_keys = list(config_dict.keys())
    
    missing = [p for p in fnp_expected_outputs if p not in dict_keys]
    extra = [k for k in dict_keys if k not in fnp_expected_outputs]
    
    if not missing and not extra:
        return True, "✅ Interfaz sincronizada."
    else:
        msg = f"❌ Error de Interfaz: Faltan {missing}, Sobran {extra}"
        return False, msg

# =============================================================================
# 3. FUNCIÓN DE PROCESAMIENTO (Nombre Genérico)
# =============================================================================

def execute_fnp_processing(
    nc_path: str,
    png_CRSnative_true_color: str,
    png_CRSnative_true_color_day_only: str,
    png_CRSwgs84_true_color: str,
    png_CRSwgs84_true_color_day_only: str,
    tif_CRSwgs84_true_color: str,
    json_meta: str,
    overwrite: bool = False
):
    """
    Ejecuta el procesamiento Satpy.
    """
    start_time = time.time()
    
    # 1. Validación de existencia
    if not overwrite and Path(png_CRSnative_true_color).exists():
        return True

    try:
        # Asegurar directorios
        Path(png_CRSnative_true_color).parent.mkdir(parents=True, exist_ok=True)

        # 2. Carga de Escena
        scn = Scene(filenames=[nc_path], reader='abi_l2_nc')
        scn.load(['true_color'])

        # --- PROCESO NATIVO ---
        scn.save_datasets(writer='simple_image', datasets=['true_color'], filename=png_CRSnative_true_color)

        # --- REPROYECCIÓN WGS84 ---
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        scn_res = scn.resample(area_def)

        # --- GUARDADO WGS84 ---
        scn_res.save_datasets(writer='simple_image', datasets=['true_color'], filename=png_CRSwgs84_true_color)
        scn_res.save_datasets(writer='geotiff', datasets=['true_color'], filename=tif_CRSwgs84_true_color)

        # 3. METADATA
        duration = round(time.time() - start_time, 2)
        if json_meta:
            with open(json_meta, 'w') as f:
                json.dump({
                    "input_file": Path(nc_path).name,
                    "duration_sec": duration,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=4)

        # Limpieza
        del scn; del scn_res; gc.collect()
        return True

    except Exception as e:
        print(f"❌ [FNP ERROR] {e}")
        return False

# =============================================================================
# 4. AUTO-VERIFICACIÓN AL IMPORTAR
# =============================================================================
status, report = verify_fnp_interface(dict_output_schema, execute_fnp_processing)
if not status:
    print(f"⚠️ Advertencia de consistencia: {report}")
