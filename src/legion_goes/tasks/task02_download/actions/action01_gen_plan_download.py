# =============================================================================
# FILE PATH: src/legion_goes/tasks/task02_download/actions/action01_gen_plan_download.py
# Version: 1.1.2 (SOT Synchronized & Variable Fix)
# =============================================================================

import json
import itertools
from datetime import datetime, timezone
from pathlib import Path

# SoT Imports
from legion_goes.SoT.goes_sat  import get_sat_info
from legion_goes.SoT.goes_prod import get_product_info

# Action Tools
from .fn01_file_name_plan_download import (
    generate_plan_download_file_path,
    validate_params
)

# --- HELPER FUNCTIONS ---

def generate_dict_self_info(file_path: Path) -> dict:
    """Generates metadata about the Download Plan file itself."""
    now = datetime.now()
    return {
        "description": "Download Plan for 1 day, for 1 specific product.",
        "version_github": "v.0.0.1",
        "file_name": file_path.name,
        "path_absolute": str(file_path.resolve()),
        "created_at_local": now.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_expected_names(product_id: str, sat_id_num: str, str_year: str, str_day: str) -> list:
    prod_info = get_product_info(product_id)
    date_prefix = f"{str_year}{str_day}"
    time_info = prod_info['default_time']
    
    raw_times = [
        f"{h}{m}{s}".strip() 
        for h, m, s in itertools.product(
            time_info['hours'], 
            time_info['minutes'], 
            time_info['seconds']
        )
    ]
    
    file_prefix = f"{prod_info['init_file_name']}{sat_id_num}_s"
    return [f"{file_prefix}{date_prefix}{t}" for t in raw_times]

def generate_dict_inventory(list_expected: list, bucket: str, product_id: str, str_year: str, str_day: str, out_base: Path) -> dict:
    inventory = {}
    total = len(list_expected)
    max_d = len(str(total))
    
    # Usamos la llave unificada de tu SoT v.1.0.1
    prod_SoT_info = get_product_info(product_id)
    selected_cadence = prod_SoT_info["cadence_full_disk"]
    
    time_format = "YYYYDDDHHMMSS"
    
    for i, filename in enumerate(list_expected, 1):
        t_id = filename.split('_s')[-1]
        str_hour = t_id[7:9] if len(t_id) >= 9 else "00"
        
        rel_folder = Path(bucket) / product_id / str_year / str_day / str_hour
        abs_folder = (out_base / rel_folder).resolve()
        
        key = f"file{i:0{max_d}d}"
        inventory[key] = {
            "pos": f"{i:0{max_d}d}/{total:0{max_d}d}",
            "timestamp": t_id,
            "time_format": time_format[0:len(t_id)],
            "cadence": selected_cadence,
            "year" : str_year,
            "day" : str_day,
            "hour": str_hour,
            "status": {
                "is_ready": True, 
                "exists_online": None, 
                "exists_local": None, 
                "is_done": None
            },
            "file_s3": {
                "bucket": bucket,
                "prefix_day": f"{product_id}/{str_year}/{str_day}",
                "prefix_hour": f"{product_id}/{str_year}/{str_day}/{str_hour}",
                "init_name": filename,
                "file_name": None,
                "file_exists": None,
                "size_mb": None
            },
            "file_local": {
                "init_name": filename, 
                "file_name": None,
                "path_relative": None,
                "path_absolute": None,
                "file_exists": None,
                 "size_mb": None
                 },
            "folder_local": {
                "path_relative": str(rel_folder),
                "path_absolute": str(abs_folder)
            }
        }
    return inventory

# --- CORE ORCHESTRATION ---

def generate_dict_plan_download(sat_id: str, year: str, day: str, product_id: str, output_folder_base: str):
    str_day = str(day).zfill(3)
    str_year = str(year)
    out_base = Path(output_folder_base)

    validate_params(year=str_year, day=str_day, sat_id=sat_id, product_id=product_id)
    
    sat_SoT_info = get_sat_info(sat_id) 
    bucket_name = sat_SoT_info['bucket']
    
    prod_SoT_info = get_product_info(product_id)
    selected_cadence = prod_SoT_info["cadence_full_disk"]
    
    list_expected = generate_expected_names(product_id, sat_SoT_info["id"], str_year, str_day)
    inventory = generate_dict_inventory(list_expected, bucket_name, product_id, str_year, str_day, out_base)

    path_rel = Path(bucket_name) / product_id / str_year / str_day
    path_abs = (out_base / path_rel).resolve()
    
    the_date_now = datetime.now() 
    now_local = the_date_now.strftime("%Y-%m-%d %H:%M:%S")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    date_obj = datetime.strptime(f"{str_year}{str_day}", "%Y%j")
    date_gregorian = date_obj.strftime("%Y-%m-%d")

    return {
        "sat_prod_info": {
            "satellite": f"GOES-{sat_SoT_info['id']}", # Corregido sat_info -> sat_SoT_info
            "position": sat_SoT_info['pos'].upper(),
            "product_id": product_id,
            "cadence": selected_cadence, # Corregido typo 'candence'
            "bucket": bucket_name,
            "year": str_year,
            "day": str_day,
            "date_julian": f"{str_year}{str_day}",
            "date_gregorian": date_gregorian,
        },
        "summary": {
            "is_done": False,
            "expected_total_files": len(list_expected),
            "local_total_files": None,
            "created_at_time_local": now_local,
            "created_at_time_utc": now_utc,
            "ofyd_absolute": str(path_abs),
        },
        "download_inventory": inventory,
    }

def run_task02_download_action01_generate_plan(sat_id: str, year: str, day: str, product_id: str, output_folder_base: str, overwrite: bool = False):
    ctx = "[Action01 - Generator Plan Download]"
    path_plan = generate_plan_download_file_path(
        year=year, day=day, sat_id=sat_id, 
        product_id=product_id, output_folder_base=output_folder_base
    )

    print(f"\n{'='*65}\n🚀 {ctx}\n{'='*65}")
    
    if path_plan.exists() and not overwrite:
        print(f"⚠️  Status: Plan exists. Skipping.\n📂 Path: {path_plan}\n")
        return True

    try:
        # Generar data
        plan_data = generate_dict_plan_download(sat_id, year, day, product_id, output_folder_base)
        # Generar self_info con la ruta final
        self_info = generate_dict_self_info(path_plan)
        
        # Ensamblado con self_info al inicio
        plan_dict = {
            "self_info": self_info,
            **plan_data
        }
        
        path_plan.parent.mkdir(parents=True, exist_ok=True)
        with open(path_plan, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4)
        
        print(f"✅ Success! Plan generated.\n📂 Saved at: {path_plan}\n")
        return True
    except Exception as e:
        print(f"❌ Error during generation:\n💬 Detail: {e}\n")
        return False
