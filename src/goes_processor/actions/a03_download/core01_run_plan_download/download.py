# src/goes_processor/actions/a03_download/core01_run_plan_download/download.py

import json
import os
import time
import s3fs
from pathlib import Path
from datetime import datetime

# --- My Libraries ---
from goes_processor.HARDCODED_FOLDERS import get_my_path

# --- Constants para el CLI ---
PRODUCT_STRATEGY = {
    "ABI-L2-LSTF":   {"desc": "Land Surface Temperature"},
    "ABI-L2-MCMIPF": {"desc": "Cloud and Moisture Imagery"},
    "ABI-L2-FDCF":   {"desc": "Fire - Hot Spot Characterization"},
    "GLM-L2-LCFA":   {"desc": "Lightning Detection"},
}

PRODUCT_OPTIONS = list(PRODUCT_STRATEGY.keys()) + ["ALL"]

# --- Auxiliares ---
def get_goes_satellite_id(year, day):
    """Retorna el ID del satélite (16 o 19) según la fecha."""
    try:
        date_obj = datetime.strptime(f"{year}-{str(day).zfill(3)}", "%Y-%j")
        if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
            return "16"
        return "19"
    except:
        return "16"

def run_plan_download(year, day, product, hour, minute, overwrite=False, check_again=False):
    """
    v.0.8.2 - Restauración de visualización: [ID] Emoji Nombre | Tamaño
    """
    start_time_job = time.time()
    
    # Rutas
    base_folder_planner = Path(get_my_path("plan_download"))
    output_root = Path(get_my_path("data_raw"))
    
    target_product = product.upper()
    fs = s3fs.S3FileSystem(anon=True)
    
    sat_id = get_goes_satellite_id(year, day)
    bucket_name = f"noaa-goes{sat_id}"
    str_year, str_day = str(year), str(day).zfill(3)
    
    # 1. Cargar Planner
    planner_dir = base_folder_planner / bucket_name / str_year / str_day
    full_json_path = planner_dir / f"planner_download_{str_year}_{str_day}_{target_product}.json"
    
    if not full_json_path.exists():
        print(f"\n⚠️  Plan no encontrado: {full_json_path}")
        return

    with open(full_json_path, 'r', encoding='utf-8') as f:
        planner_data = json.load(f)

    all_files = planner_data.get("download_files", {})
    summary = planner_data.get("summary", {})
    
    filtered_files = {
        k: v for k, v in all_files.items() 
        if (hour.upper() == "ALL" or str(v.get("hour")).zfill(2) == hour.zfill(2)) and
           (minute.upper() == "ALL" or str(v.get("minutes")).zfill(2) == minute.zfill(2))
    }

    if not filtered_files:
        print(f"     ℹ️  No files match the filter {hour}:{minute}")
        return 

    # --- Header Estético ---
    total_to_process = len(filtered_files)
    padding = len(str(total_to_process))
    print(f"\n🚀 SATELLITE DOWNLOADER | {target_product}")
    print(f"{'='*90}")
    print(f"🛰️  Satellite: GOES-{sat_id} | Date: {str_year}-{str_day} | Total: {total_to_process} files")
    
    rel_folder = Path(bucket_name) / target_product / str_year / str_day
    local_dir = output_root / rel_folder
    local_dir.mkdir(parents=True, exist_ok=True)

    count_downloaded = 0
    count_exists = 0
    total_size_mb = 0
    s3_hour_cache = {}

    # --- Loop de Procesamiento ---
    for idx, (file_key, info) in enumerate(filtered_files.items(), 1):
        h_str = str(info.get("hour")).zfill(2)
        s_time_pattern = info.get("s_time")
        
        if h_str not in s3_hour_cache:
            try:
                items = fs.ls(f"{bucket_name}/{target_product}/{str_year}/{str_day}/{h_str}/", detail=True)
                s3_hour_cache[h_str] = {os.path.basename(i['name']): i['size'] for i in items}
            except: s3_hour_cache[h_str] = {}

        match_name = next((n for n in s3_hour_cache[h_str] if s_time_pattern in n), None)
        if not match_name: continue

        local_path = local_dir / match_name
        size_web_mb = round(s3_hour_cache[h_str][match_name] / (1024 * 1024), 2)
        
        should_download = True
        if local_path.exists() and not overwrite:
            if not check_again or round(os.path.getsize(local_path)/(1024*1024), 2) == size_web_mb:
                should_download = False

        if should_download:
            # FORMATO SOLICITADO: Nombre del archivo | Tamaño
            print(f"  [{str(idx).zfill(padding)}/{str(total_to_process).zfill(padding)}] ⬇️  {match_name} | {size_web_mb} MB")
            fs.get(f"{bucket_name}/{target_product}/{str_year}/{str_day}/{h_str}/{match_name}", str(local_path))
            count_downloaded += 1
        else:
            count_exists += 1

        # Metadatos
        f_size_local = round(os.path.getsize(local_path) / (1024 * 1024), 2)
        total_size_mb += f_size_local
        info.update({
            "file_name": match_name,
            "path_relative": str(rel_folder / match_name),
            "path_absolute": str(local_path.absolute()),
            "file_exist_local": True,
            "file_size_mb_local": f_size_local,
            "is_check": True
        })

    # --- Guardado y Resumen ---
    total_local_in_plan = sum(1 for f in all_files.values() if f.get("file_exist_local", False))
    duration = round(time.time() - start_time_job, 2)
    
    summary["time_last_mod"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System"
    
    if hour.upper() == "ALL" and minute.upper() == "ALL":
        summary["is_done"] = (total_local_in_plan == len(all_files))
        summary["total_files"] = total_local_in_plan
        summary["total_size_mb"] = round(total_size_mb, 2)
        summary["total_time"] = f"{duration}s"

    with open(full_json_path, 'w', encoding='utf-8') as f:
        json.dump(planner_data, f, indent=4, ensure_ascii=False)
    
    # Footer
    print(f"\n✅ PROCESS COMPLETED: {total_local_in_plan}/{len(all_files)} files in storage.")
    print(f"⏱️  Duration: {duration}s | New: {count_downloaded} | Existing: {count_exists} | Day Total: {round(total_size_mb, 2)} MB")
    print(f"{'='*90}\n")
