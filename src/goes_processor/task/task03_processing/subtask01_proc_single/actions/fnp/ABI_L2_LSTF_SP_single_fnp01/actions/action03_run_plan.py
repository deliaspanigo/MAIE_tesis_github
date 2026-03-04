"""
Path: src/goes_processor/task/task02_download/actions/action03_run_download_plan.py
Version: 0.5.2 (Ultra-Clean Version)
Description: Engine with zero-clutter output. Only prints start, downloads, and summary.
"""

import json
import s3fs
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .fn01_file_name_plan_download import get_plan_download_file_path
from goes_processor.SoT.goes_sat import get_sat_info

def _download_single_file(file_id, info, fs, overwrite):
    """Descarga silenciosa desde S3."""
    s3_meta = info['s3_metadata']
    local_meta = info['local_metadata']
    s3_pattern = f"{s3_meta['bucket']}/{s3_meta['key_prefix']}/{s3_meta['init_name']}*.nc"
    
    try:
        found_files = fs.glob(s3_pattern)
        if not found_files:
            return file_id, {"status": "NOT_FOUND"}
        
        remote_path = found_files[0]
        file_name = Path(remote_path).name
        local_full_path = Path(local_meta['folder_absolute']) / file_name
        
        if local_full_path.exists() and not overwrite:
            return file_id, {"status": "SKIPPED"}
        
        local_full_path.parent.mkdir(parents=True, exist_ok=True)
        fs.get(remote_path, str(local_full_path))
        
        size_mb = round(local_full_path.stat().st_size / (1024 * 1024), 2)
        return file_id, {"status": "SUCCESS", "file_name": file_name, "size": size_mb}
    except:
        return file_id, {"status": "ERROR"}

def execute_action_run_download(sat_id, product, year, day, threads=8, overwrite=False):
    """Orquestador sin prints intermedios."""
    sat_data = get_sat_info(sat_id)
    real_id = str(sat_data["id"]).upper().replace("G", "")
    day_str = str(day).zfill(3)
    path_plan = get_plan_download_file_path(year, day_str, real_id, product)
    
    with open(path_plan, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)
    
    inventory = plan_data['inventory']
    fs = s3fs.S3FileSystem(anon=True)
    
    # Único print de inicio
    print(f"🚀 Starting download: {product} | {year}-{day_str} | Threads: {threads}")
    
    status_counts = {"SUCCESS": 0, "SKIPPED": 0, "ERROR": 0, "NOT_FOUND": 0}
    tasks_to_run = {}

    # Verificación silenciosa
    for fid, info in inventory.items():
        folder = Path(info['local_metadata']['folder_absolute'])
        init_name = info['s3_metadata']['init_name']
        actual_files = list(folder.glob(f"{init_name}*.nc"))

        if actual_files and not overwrite:
            status_counts["SKIPPED"] += 1
            inventory[fid]['status']['is_downloaded'] = True
        else:
            tasks_to_run[fid] = info

    # Descarga
    if tasks_to_run:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(_download_single_file, fid, info, fs, overwrite): fid 
                       for fid, info in tasks_to_run.items()}
            
            for future in as_completed(futures):
                fid, res = future.result()
                s_type = res['status']
                if s_type == "SUCCESS":
                    inventory[fid]['status']['is_downloaded'] = True
                    # Solo imprimimos si realmente bajamos algo nuevo
                    print(f" ✅ {res['file_name']} ({res['size']} MB)")
                status_counts[s_type] += 1

    # Guardado silencioso
    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=4)
        
    # Único print final
    total_ready = status_counts["SUCCESS"] + status_counts["SKIPPED"]
    print(f"🏁 Finished. Successfully synced: {total_ready}/{len(inventory)} files.")
    
    return True
