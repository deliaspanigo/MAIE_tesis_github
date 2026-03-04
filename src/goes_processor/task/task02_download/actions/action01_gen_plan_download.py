"""
Path: src/goes_processor/task/task02_download/actions/action01_gen_plan_download.py
Version: 0.7.0 (Correct Schema Edition)
"""

import json
import itertools
from datetime import datetime
from pathlib import Path

from goes_processor.SoT import goes_prod
from goes_processor.SoT.goes_sat import get_sat_info
from .fn01_file_name_plan_download import get_plan_download_file_path

def generate_inventory(list_spected_names: list, bucket: str, prod_id: str, str_year: str, str_day: str, output_folder_base: Path):
    """CONSTRUCTOR DE INVENTARIO: Mantiene la jerarquía completa de llaves."""
    inventory_files = {}
    total_expected = len(list_spected_names)
    max_digits = len(str(total_expected))

    for counter, selected_file in enumerate(list_spected_names, 1):
        t_id = selected_file.split('_s')[-1]
        hour_folder = t_id[7:9] if len(t_id) >= 9 else "00"
        
        folder_path_part = Path(bucket) / prod_id / str_year / str_day / hour_folder
        full_folder_path = (output_folder_base / folder_path_part).resolve()
        
        file_key = f"file{counter:0{max_digits}d}"
        
        inventory_files[file_key] = {
            "pos_file": f"{counter:0{max_digits}d} of {total_expected:0{max_digits}d}",
            "time_stamp": t_id,
            "mini_summary": {
                "is_ready": True, 
                "exists_online": None, 
                "exists_local": None, 
                "is_done": False
            },
            "file_s3": {
                "bucket": bucket,
                "prefix_hour": f"{prod_id}/{str_year}/{str_day}/{hour_folder}",
                "init_name": selected_file,
                "file_name": None
            },
            "file_local": {  # <--- AQUÍ ESTÁ LA LLAVE QUE FALTABA
                "init_name": selected_file,
                "file_name": None,
                "file_exists": False,
                "size_mb": None,
                "path_absolute": None,
                "path_relative": None
            },
            "folder_local": {
                "path_relative": str(folder_path_part),
                "path_absolute": str(full_folder_path),
                "folder_exists": None 
            }
        }
    
    return inventory_files

def get_dict_plan_download(sat_pos: str, year: int, day: int, prod_id: str, output_folder_base: str):
    out_base = Path(output_folder_base)
    str_day = str(day).zfill(3)
    str_year = str(year)
    date_prefix = str_year + str_day

    # Inferencia histórica correcta (GOES-19 para 2026 East)
    sat_data = get_sat_info(sat_pos, year=str_year, day=str_day)
    final_sat_id = sat_data["id"]
    final_bucket = sat_data["bucket"]
    
    the_prod_info = goes_prod.get_product_info(prod_id=prod_id)
    
    time_info = the_prod_info['default_time']
    raw_times = [f"{h}{m}{s}".strip() for h, m, s in itertools.product(time_info['hours'], time_info['minutes'], time_info['seconds'])]
    
    # Prefijo con G16, G17, G18 o G19 según la fecha
    file_prefix = f"{the_prod_info['init_file_name']}{final_sat_id}_s"
    list_spected_names = [f"{file_prefix}{date_prefix}{t}" for t in raw_times]

    inventory = generate_inventory(list_spected_names, final_bucket, prod_id, str_year, str_day, out_base)

    super_time_info = datetime.now().isoformat()
    
    return {
        "sat_prod_info": {
            "satellite": sat_data["name06"],
            "sat_position": sat_pos.upper(),
            "product_id": prod_id,
            "bucket_name": final_bucket,
            "year": str_year,
            "day": str_day,
            "date_julian": f"{year}{str_day}",
            "prefix_day": f"{prod_id}/{str_year}/{str_day}",
        },
        "summary": {
            "is_done": False,
            "total_files_expected": len(list_spected_names),
            "total_files_done": 0,
            "timestamp_file_creation": super_time_info,
            "timestamp_file_last_mod": super_time_info,
        },
        "download_inventory": inventory,
    }

def gen_and_save_plan_download(sat_pos: str, year: int, day: int, prod_id: str, output_folder_base: str, overwrite: bool):
    ctx = "[Action01]"
    path_plan = get_plan_download_file_path(str(year), str(day).zfill(3), sat_pos, prod_id)
    
    if path_plan.exists() and not overwrite:
        print(f"  ⚠️ {ctx}: Plan exists. Skipping.")
        return True

    dict_plan = get_dict_plan_download(sat_pos, year, day, prod_id, output_folder_base)
    
    try:
        path_plan.parent.mkdir(parents=True, exist_ok=True)
        with open(path_plan, 'w', encoding='utf-8') as f:
            json.dump(dict_plan, f, indent=4)
        print(f"  ✅ {ctx}: Success! Plan saved for {dict_plan['sat_prod_info']['satellite']}")
        return True
    except Exception as e:
        print(f"  ❌ {ctx}: Error: {e}")
        return False
