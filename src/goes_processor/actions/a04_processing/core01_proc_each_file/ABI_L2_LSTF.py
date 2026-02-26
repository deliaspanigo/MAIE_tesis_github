# src/goes_processor/actions/a04_processing/core01_proc_each_file/ABI_L2_LSTF.py

import json
import os
import time
from pathlib import Path
from datetime import datetime

# --- Satpy & Resampling ---
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- My Libraries ---
from goes_processor.HARDCODED_FOLDERS import get_my_path

def process_lstf_single_file(dict_selected_proc, overwrite=False, indent=""):
    """
    Sequential Orchestrator for LST Module.
    Restaurado con lógica completa v.0.5.1.
    """
    success_report = {"stage_01": False}
    
    # Execute Stage 01
    success_report["stage_01"] = fn01_lstf_generate_products(dict_selected_proc, overwrite, indent)
    
    return success_report

# --- STAGE FUNCTIONS ---

def fn01_lstf_generate_products(dict_selected_proc, overwrite, indent=""):
    """
    Stage 01: Multi-Product Generation (Grayscale Celsius & Custom Color).
    Incluye resampling WGS84 y exportación múltiple.
    """
    
    # 1. ENTRADAS
    str_fpa_input_file_path_nc = dict_selected_proc["inputs"]["raw_nc"]["path_absolute"]
    file_path = Path(str_fpa_input_file_path_nc) # FIX para evitar NameError
    
    # 2. SALIDAS (Sincronizado con nombres de llaves de tu lstf.py)
    fn01_data = dict_selected_proc["outputs"]["fn01"]
    paths_abs = fn01_data["dict_file_path_absolute"]
    
    str_fpa_goes_east_grey_png  = paths_abs["goes_east_grey_png"]
    str_fpa_goes_east_color_png = paths_abs["goes_east_color_png"]
    str_fpa_wgs84_grey_png      = paths_abs["wgs84_grey_png"]
    str_fpa_wgs84_color_png     = paths_abs["wgs84_color_png"]
    str_fpa_wgs84_grey_tif      = paths_abs["wgs84_grey_tif"]
    str_fpa_wgs84_color_tif     = paths_abs["wgs84_color_tif"]
    str_fpa_metadata_json       = paths_abs["metadata_json"]
    
    str_fpa_output_folder       = Path(fn01_data["folder_absolute"])

    # Rutas de Sistema
    path_cache = get_my_path("proc_core01", ".cache_pyresample")

    # 3. VERIFICACIONES PREVIAS
    if not file_path.exists():
        print(f"{indent}❌ [fn01] Input file missing: {file_path.name}")
        return False

    if Path(str_fpa_wgs84_color_png).exists() and not overwrite:
        print(f"{indent}⏩ [fn01] Skipped: Files already exist.")
        return True

    start_ts = time.time()
    
    try:
        str_fpa_output_folder.mkdir(parents=True, exist_ok=True)
        print(f"{indent}⏰ [fn01] Start: {datetime.now().strftime('%H:%M:%S')}")

        # --- LÓGICA SATPY ---
        # 4. CARGA (1/6)
        print(f"{indent}📖 [fn01] [1/6] Loading Scene...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        
        prod_raw   = 'LST'
        prod_color = 'lst_celsius_color01' # Tu producto custom
        
        scn.load([prod_raw])
        
        # Conversión a Celsius
        scn[prod_raw] = scn[prod_raw] - 273.15
        scn[prod_raw].attrs['units'] = 'Celsius'
        
        # Generar versión color (si está en tus composites)
        try:
            scn.load([prod_color])
        except Exception:
            print(f"{indent}⚠️ [fn01] Composite {prod_color} not found, skipping color.")
            prod_color = None

        # 5. EXPORTACIÓN NATIVA (2/6)
        print(f"{indent}📸 [fn01] [2/6] Saving Native PNGs...")
        scn.save_dataset(prod_raw, filename=str_fpa_goes_east_grey_png, writer='simple_image')
        if prod_color:
            scn.save_dataset(prod_color, filename=str_fpa_goes_east_color_png)

        # 6. RESAMPLING (3/6)
        print(f"{indent}🔄 [fn01] [3/6] Resampling to WGS84...")
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 
                                  3600, 1800, [-180, -90, 180, 90])
        
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=str(path_cache))

        # 7. EXPORTACIÓN FINAL (4/6 y 5/6)
        print(f"{indent}💾 [fn01] [4/6] Saving GeoTIFFs...")
        scn_res.save_dataset(prod_raw, filename=str_fpa_wgs84_grey_tif, writer='geotiff')
        if prod_color:
            scn_res.save_dataset(prod_color, filename=str_fpa_wgs84_color_tif, writer='geotiff')

        print(f"{indent}📸 [fn01] [5/6] Saving WGS84 PNGs...")
        scn_res.save_dataset(prod_raw, filename=str_fpa_wgs84_grey_png, writer='simple_image')
        if prod_color:
            scn_res.save_dataset(prod_color, filename=str_fpa_wgs84_color_png)

        # 8. METADATOS (6/6)
        print(f"{indent}📸 [fn01] [6/6] Saving Metadata JSON...")
        duration = round((time.time() - start_ts) / 60, 2)
        meta_audit = {
            "p_info": {
                "process_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "duration_min": duration,
                "input": file_path.name
            },
            "status": "SUCCESS"
        }
        
        with open(str_fpa_metadata_json, 'w') as f:
            json.dump(meta_audit, f, indent=4)

        print(f"{indent}✅ [fn01] Complete in {duration} min.")
        return True

    except Exception as e:
        print(f"{indent}❌ [fn01] ERROR: {str(e)}")
        return False
