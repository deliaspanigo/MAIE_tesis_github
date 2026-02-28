# =============================================================================
# FILE PATH: src/goes_processor/actions/a02_planning/core01_planner_download/code01_gen_plan_download.py
# Version: 0.1.8 (Full SoT Integration & Dual-Layer Guard)
# =============================================================================

# 1. CAPA DE SISTEMA
try:
    import json
    import itertools
    from datetime import datetime
    from pathlib import Path
except ImportError as e:
    print(f"\n[SYSTEM LIB ERROR] - Critical libraries missing: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO
try:
    from goes_processor.SoT.goes_hardcoded_folders import get_my_path
    from goes_processor.SoT.goes_sat import get_goes_id_by_julian_date, get_satellite_info
    from goes_processor.SoT.goes_prod import SAVED_INFO_PROD_GOES, AVAILABLE_GOES_PRODUCTS
    from goes_processor.SoT.goes_sat import AVAILABLE_GOES_SAT_POSITIONS
    from .fn01_file_name_plan_download import get_plan_download_file_name, get_plan_download_file_path
except ImportError as e:
    print(f"\n[PROJECT LIB ERROR] - Internal modules missing: {e}\n")
    raise SystemExit(1)

def general_control(sat_position: str, product_id: str, year: str, day: str):
    """Strict validation before plan generation."""
    ctx = "[CONTROL - code01_gen_plan_download.py]"
    
    if sat_position not in AVAILABLE_GOES_SAT_POSITIONS:
        raise ValueError(f"{ctx} Invalid position '{sat_position}'.")
    
    if product_id not in AVAILABLE_GOES_PRODUCTS:
        raise ValueError(f"{ctx} Product '{product_id}' not found in SoT.")
    
    if not (str(year).isdigit() and len(str(year)) == 4):
        raise ValueError(f"{ctx} Year '{year}' must be YYYY.")
        
    if not (str(day).isdigit() and len(str(day)) == 3 and 1 <= int(day) <= 366):
        raise ValueError(f"{ctx} Day '{day}' must be DDD (001-366).")

def generate_download_plan_day(sat_position: str, product_id: str, year: str, day: str) -> dict:
    """
    Generates the planning JSON by reading configuration from SoT.
    """
    ctx = "[Planning - generate_download_plan_day()]"
    
    try:
        general_control(sat_position, product_id, year, day)

        # --- RECOLECCIÓN DE METADATA DESDE SOT ---
        sat_id = get_goes_id_by_julian_date(year, day, sat_position=sat_position)
        sat_info = get_satellite_info(sat_id)
        prod_info = SAVED_INFO_PROD_GOES[product_id] 
        
        bucket = sat_info["bucket"]
        init_fn = prod_info["init_file_name"]
        total_expected = prod_info["total_files_one_day"]
        
        # Manejo de tiempos (Hours, Mins, Secs)
        d_time = prod_info["default_time"]
        hrs = d_time.get("hours") or [""]
        mins = d_time.get("minutes") or [""]
        secs = d_time.get("seconds") or [""]

        # Timestamp generation (Format: YYYYJJJHHMMSS)
        time_slots = sorted(["".join(filter(None, [year, day, h, m, s])) 
                            for h, m, s in itertools.product(hrs, mins, secs)])

        # --- CONSTRUCCIÓN DEL INVENTARIO ---
        inventory_files = {}
        goes_raw_root = get_my_path("data_raw")
        max_digits = len(str(total_expected))

        for counter, t_id in enumerate(time_slots, 1):
            selected_file = f"{init_fn}{sat_id}_s{t_id}"
            
            # Local Folder Structure: bucket / product / year / day / hour
            hour_folder = t_id[7:9] if len(t_id) >= 9 else "00"
            folder_path_part = Path(bucket) / product_id / year / day / hour_folder
            
            file_key = f"file{counter:0{max_digits}d}"
            
            inventory_files[file_key] = {
                "pos_file": f"{counter:0{max_digits}d} of {total_expected:0{max_digits}d}",
                "time_stamp": t_id,
                "mini_summary": {"is_ready": True, "is_done": False, "time_last_mod": None},
                "file_s3": {
                    "bucket": bucket,
                    "prefix": f"{product_id}/{year}/{day}/{hour_folder}",
                    "regex": f"{selected_file}*.nc",
                    "file_exists_web": False,
                },
                "file_local": {
                    "file_name_expected": f"{selected_file}.nc",
                    "path_absolute": str((goes_raw_root / folder_path_part / f"{selected_file}.nc").resolve()),
                    "path_relative": None, 
                    "file_exists_local": False,
                    "file_size_mb_local": None,
                },
                "folder_local": {
                    "path_absolute": str((goes_raw_root / folder_path_part).resolve()),
                    "folder_exists_local": False
                }
            }

        # --- ENSAMBLAJE FINAL ---
        path_plan = get_plan_download_file_path(year, day, sat_id, sat_position, product_id)
        
        return {
            "sat_prod_info": {
                "satellite": f"GOES-{sat_id}",
                "sat_position": sat_position,
                "product_id": product_id,
                "bucket_name": bucket,
                "date_julian": f"{year}{day}",
                "total_files_one_day": total_expected,
            },
            "summary": {
                "is_done": False,
                "total_files_expected": total_expected,
                "total_files_ready": 0,
                "time_file_creation": datetime.now().isoformat(),
            },
            "plan_download_self_info": {
                "file_name": get_plan_download_file_name(year, day, sat_id, sat_position, product_id),
                "path_absolute": str(path_plan.resolve())
            },
            "download_inventory": inventory_files,
        }

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None
