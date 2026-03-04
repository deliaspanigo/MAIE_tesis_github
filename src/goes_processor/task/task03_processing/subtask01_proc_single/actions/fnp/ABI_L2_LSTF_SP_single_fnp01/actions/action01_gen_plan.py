"""
Path: src/goes_processor/task/task02_download/actions/action01_gen_plan_download.py
Description: Generates the JSON download plan with clean G-ID normalization.
"""

import json
from pathlib import Path
from itertools import product
from goes_processor.SoT.goes_sat import get_sat_info
from goes_processor.SoT.goes_prod import get_product_info
from .fn01_file_name_plan_download import get_plan_download_file_path

def execute_action_gen_plan(sat_id: str, product_id: str, year: str, day: str, overwrite: bool = True):
    ctx = "[task02_download - action01 - execute_action_gen_plan()]"
    
    # 1. Obtener Metadata del SoT
    sat_data = get_sat_info(sat_id)
    prod_info = get_product_info(product_id)
    
    # 2. NORMALIZACIÓN CRÍTICA DEL ID (G16, G17, G18, G19)
    # Si sat_data['id'] es "19", real_id será "19"
    # Si sat_data['id'] es "G19", real_id será "19" (limpiamos para evitar GG19)
    real_id = str(sat_data["id"]).upper().replace("G", "")
    day_str = str(day).zfill(3)
    
    # 3. Definir Ruta del Plan
    path_plan = get_plan_download_file_path(year, day_str, real_id, product_id)
    if path_plan.exists() and not overwrite:
        return path_plan

    # 4. Construcción del Prefijo del Archivo (Limpieza de Doble G)
    # Tomamos el prefijo del SoT (ej: "OR_ABI-L2-LSTF-M6_G") 
    # y nos aseguramos de que termine en G exactamente una vez.
    base_prefix = str(prod_info['init_file_name'])
    if not base_prefix.endswith("_G"):
        # Si por error en el SoT no tiene la G, se la ponemos
        if "_G" not in base_prefix:
            base_prefix += "_G"
    
    inventory = {}
    
    # 5. Generar combinaciones de tiempo
    t_config = prod_info['default_time']
    time_combinations = list(product(t_config['hours'], t_config['minutes'], t_config['seconds']))
    
    for idx, (h, m, s) in enumerate(time_combinations, 1):
        # El timestamp que busca NOAA: YYYYJJJHHMM (Year, Day, Hour, Minute)
        t_id = f"{year}{day_str}{h}{m}{s}"
        
        # EL NOMBRE CLAVE: Prefijo (termina en _G) + ID (19) + _s + Timestamp
        # Resultado: OR_ABI-L2-LSTF-M6_G19_s202600300
        init_name = f"{base_prefix}{real_id}_s{t_id}"
        
        file_key = f"file_{idx:02d}"
        inventory[file_key] = {
            "s3_metadata": {
                "bucket": f"noaa-goes{real_id}",
                "key_prefix": f"{product_id}/{year}/{day_str}/{h}",
                "init_name": init_name
            },
            "local_metadata": {
                "folder_absolute": f"/home/legion/bulk/MAIE_tesis2026/f01_code/MAIE_tesis_github/data_raw/noaa-goes{real_id}/{product_id}/{year}/{day_str}/{h}"
            },
            "status": {
                "is_downloaded": False,
                "file_name_final": None,
                "size_mb": 0
            }
        }

    # 6. Guardar JSON
    path_plan.parent.mkdir(parents=True, exist_ok=True)
    plan_output = {
        "metadata": {
            "sat_id": real_id,
            "product": product_id,
            "day_julian": day_str,
            "year": year
        },
        "inventory": inventory
    }
    
    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_output, f, indent=4)
        
    print(f"✅ [SUCCESS] Plan generated with {len(inventory)} entries (Target: G{real_id})")
    return path_plan
