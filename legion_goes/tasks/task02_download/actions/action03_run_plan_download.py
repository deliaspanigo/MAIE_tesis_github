# =============================================================================
# PATH: src/legion_goes/tasks/task02_download/actions/action03_run_plan_download.py
# Version: 1.9.8 (UI: FID + FNAME + SIZE + 4 Threads | run_action Standard)
# =============================================================================

import os
import boto3
import threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config

# --- ABSOLUTE IMPORTS ---
from legion_goes.tasks.task02_download.actions.fn_utils.load_dict_plan_file_json import load_dict_plan_file_json
from legion_goes.tasks.task02_download.actions.fn_utils.save_dict_plan_json import save_dict_plan_json
from legion_goes.tasks.task02_download.actions.fn_utils.generate_plan_download_file_path import generate_plan_download_file_path
from legion_goes.tasks.task02_download.actions.fn_act02.step02_update_dict_parts.update_dict03_inventory import update_one_item_inventory_download
from legion_goes.tasks.task02_download.actions.fn_act02.update_dict_plan_download import update_dict_plan_download

lock = threading.Lock()
checkpoint_counter = 0

# --- 1. ATOMIC WORKER ---

def download_s3_item_worker(fid, info, s3_client):
    """Downloads a single file from S3 to local storage."""
    bucket = info["file_s3"]["bucket"]
    prefix = info["file_s3"]["prefix_hour"]
    init_name = info["file_s3"]["init_name"]
    
    real_filename = info["file_s3"].get("file_name")
    s3_size_bytes = int(info["file_s3"].get("size_mb", 0) * 1024 * 1024)

    try:
        if not real_filename:
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/{init_name}")
            if 'Contents' not in response: return fid, "404", "Unknown", 0
            obj = response['Contents'][0]
            s3_full_key = obj['Key']
            s3_size_bytes = obj['Size']
            real_filename = s3_full_key.split('/')[-1]
        else:
            s3_full_key = f"{prefix}/{real_filename}"

        dest_folder = Path(info["folder_local"]["path_absolute"])
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        final_path = dest_folder / real_filename
        tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

        s3_client.download_file(bucket, s3_full_key, str(tmp_path))

        local_size_mb = round(tmp_path.stat().st_size / (1024 * 1024), 2)
        
        # Validation: check if downloaded size matches S3 size
        if abs(tmp_path.stat().st_size - s3_size_bytes) < (0.5 * 1024 * 1024):
            if final_path.exists(): os.remove(final_path)
            tmp_path.rename(final_path)
            return fid, "SUCCESS", real_filename, local_size_mb
        else:
            if tmp_path.exists(): os.remove(tmp_path)
            return fid, "SIZE_ERROR", real_filename, local_size_mb
            
    except Exception as e:
        return fid, "ERR", real_filename or "Error_File", 0

# --- 2. MAIN ACTION ORCHESTRATOR ---

def run_action(sat_id, product_id, year, day, threads=4, checkpoint_n=10):
    """Entry point for the download execution."""
    global checkpoint_counter
    
    # 1. File path json.
    # 2. Check if file json exists,
    # 3. Import json.
    # 4. Check if import well.
    # 5. Update plan
    
    
    # 1. File path
    path_json = generate_plan_download_file_path(sat_id=sat_id, product_id=product_id, year=year, day=day)
    
    # 2. Check if file json exists,
    # Verifica si el archivo existe localmente...
     
    # 3. Import json.
    plan_data = load_dict_plan_file_json(path_json=str(path_json))
    if not plan_data: 
        print(f"❌ Error: Could not load plan at {path_json}")
        return False

    # 4. Check if import well.
    # Verifica si es un diccionario...
    
    
    # 5. Update  plan
    plan_data = update_dict_plan_download(dict_plan=plan_data)
    
    
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket = plan_data['sat_prod_info']['bucket']
    prefix_day = f"{plan_data['sat_prod_info']['product_id']}/{plan_data['sat_prod_info']['year']}/{plan_data['sat_prod_info']['day']}/"

    # Pre-mapping S3 names to ensure metadata is present before UI printing
    print(f"🔍 [SCANNING] Mapping S3 files for {sat_id}...")
    s3_online_files = {}
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix_day):
        if 'Contents' in page:
            for obj in page['Contents']:
                filename = obj['Key'].split('/')[-1]
                s3_online_files[filename] = obj

    inventory = plan_data["inventory"]
    total_download_bytes = 0
    for fid, info in inventory.items():
        init_name = info["file_s3"]["init_name"]
        match = next((name for name in s3_online_files if name.startswith(init_name)), None)
        if match:
            sz = s3_online_files[match]['Size']
            info["status"]["exists_online"] = True
            info["file_s3"].update({"file_name": match, "size_mb": round(sz/(1024**2), 2)})
            if not info["status"].get("is_done"): total_download_bytes += sz
        else:
            info["status"]["exists_online"] = False

    queue = {fid: info for fid, info in inventory.items() if not info["status"].get("is_done") and info["status"].get("exists_online")}
    if not queue:
        print("✨ [SKIP] No new files to download.")
        return True

    # UI Setup & Queue Execution
    total_q = len(queue)
    the_num_char = len(str(total_q)) # Fix: len(str(int)) instead of len(int)
    done = 0

    print("="*120)
    print(f"🚀 [START] Downloading {total_q} files ({round(total_download_bytes/(1024**2),2)} MB) using {threads} threads.")
    print(f"{'PROGRESS':<10} | {'FID':<10} | {'S3 FILENAME':<75} | {'SIZE':<10} | {'STATUS'}")
    print("-" * 120)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Create the futures map
        futures = {executor.submit(download_s3_item_worker, fid, info, s3_client): fid for fid, info in queue.items()}
        
        for future in as_completed(futures):
            fid, status, fname, fsize = future.result()
            with lock:
                done += 1
                # Use total_q instead of the undefined total_files
                prog_str = f"[{done:0{the_num_char}}/{total_q}]"
                
                if status == "SUCCESS":
                    # Update local inventory state
                    inventory[fid] = update_one_item_inventory_download(inventory[fid])
                    checkpoint_counter += 1
                    print(f"{prog_str:<10} | {fid:<10} | {fname:<75} | {fsize:>7} MB | \033[92m[OK]\033[0m ✅")
                else:
                    print(f"{prog_str:<10} | {fid:<10} | {fname:<75} | {fsize:>7} MB | \033[91m[{status}]\033[0m ❌")

                # Checkpoint: Save JSON periodically
                if checkpoint_counter >= checkpoint_n:
                    save_dict_plan_json(dict_plan=plan_data, path_json=str(path_json))
                    checkpoint_counter = 0

    # Final save
    save_dict_plan_json(dict_plan=plan_data, path_json=str(path_json))
    print("="*120 + "\n✅ Download process finished.")
    return True

# --- 3. MAIN (Unit Test) ---

if __name__ == "__main__":
    test_params = {"sat_id": "19", "product_id": "ABI-L2-MCMIPF", "year": "2026", "day": "003"}
    run_action(**test_params, threads=4)
