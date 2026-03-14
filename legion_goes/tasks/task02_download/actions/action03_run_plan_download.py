# =============================================================================
# PATH: legion_goes/tasks/task02_download/actions/action03_run_plan_download.py
# Version: 1.9.14 (Architecture Sync + Full Main Diagnostic)
# =============================================================================

import os
import boto3
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config

# --- ABSOLUTE IMPORTS ---
from legion_goes.code.python_sp.f99_common.load_dict_plan_from_json_file import load_dict_plan_from_json_file
from legion_goes.code.python_sp.f99_common.save_dict_plan_as_json_file import save_dict_plan_as_json_file
from legion_goes.code.python_sp.f01_donwload.utils.generate_plan_download_json_file_path import generate_plan_download_json_file_path

from legion_goes.tasks.task02_download.actions.fn_act02.step02_update_dict_parts.update_dict03_inventory import update_one_item_inventory_download
from legion_goes.tasks.task02_download.actions.fn_act02.update_dict_plan_download import update_dict_plan_download

lock = threading.Lock()
checkpoint_counter = 0

# --- 1. ATOMIC WORKER ---

def download_s3_item_worker(fid, info, s3_client):
    """Worker adjusted for v.1.7.x Hard/Soft structure."""
    try:
        defin = info["definition"]
        s3_meta = defin.get("s3_metadata", {}).get("hard", {})
        bucket = s3_meta.get("bucket")
        prefix = s3_meta.get("prefix_hour")
        
        dest_folder_str = defin.get("local_folder_info", {}).get("hard", {}).get("folder_path_absolute")
        if not dest_folder_str:
            return fid, "MISSING_PATH", "Unknown", 0
        
        dest_folder = Path(dest_folder_str)
        track = info["tracking"]
        real_filename = track.get("file_name")
        s3_size_mb = track.get("file_size_mb_online", 0)
        s3_size_bytes = int(s3_size_mb * 1024 * 1024)

        if not real_filename:
            return fid, "MISSING_NAME", "Unknown", 0

        s3_full_key = f"{prefix}/{real_filename}"
        dest_folder.mkdir(parents=True, exist_ok=True)
        final_path = dest_folder / real_filename
        
        # Check integrity
        if final_path.exists() and abs(final_path.stat().st_size - s3_size_bytes) < 1024:
            return fid, "ALREADY_DONE", real_filename, s3_size_mb

        tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        s3_client.download_file(bucket, s3_full_key, str(tmp_path))

        local_size_bytes = tmp_path.stat().st_size
        local_size_mb = round(local_size_bytes / (1024 * 1024), 2)
        
        if abs(local_size_bytes - s3_size_bytes) < (0.5 * 1024 * 1024):
            if final_path.exists(): os.remove(final_path)
            tmp_path.rename(final_path)
            return fid, "SUCCESS", real_filename, local_size_mb
        else:
            if tmp_path.exists(): os.remove(tmp_path)
            return fid, "SIZE_ERR", real_filename, local_size_mb
            
    except Exception as e:
        return fid, f"ERR_{type(e).__name__}", "Error", 0

# --- 2. MAIN ACTION ORCHESTRATOR ---

def run_action(sat_id, product_id, year, day, threads=4, checkpoint_n=10):
    global checkpoint_counter
    
    path_json = generate_plan_download_json_file_path(sat_id=sat_id, product_id=product_id, year=year, day=day)
    plan_data = load_dict_plan_from_json_file(path_json=str(path_json))
    
    if not plan_data: 
        print(f"❌ Error: Plan file not found at {path_json}")
        return False

    plan_data = update_dict_plan_download(dict_plan=plan_data)
    
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    inventory = plan_data["inventory"]
    
    first_key = next(iter(inventory))
    s3_meta = inventory[first_key]["definition"]["s3_metadata"].get("hard", {})
    bucket = s3_meta.get("bucket")
    prefix_day = s3_meta.get("prefix_day")

    if not bucket:
        s3_meta = inventory[first_key]["definition"]["s3_metadata"]
        bucket = s3_meta.get("bucket")
        prefix_day = s3_meta.get("prefix_day")

    print(f"📡 [SCANNING] Mapping S3 files for {prefix_day}...")
    s3_online_files = {}
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix_day):
        if 'Contents' in page:
            for obj in page['Contents']:
                fname = obj['Key'].split('/')[-1]
                s3_online_files[fname] = obj

    total_download_bytes = 0
    for fid, info in inventory.items():
        s3_meta_item = info["definition"]["s3_metadata"].get("hard", info["definition"]["s3_metadata"])
        init_name = s3_meta_item.get("init_name")
        match = next((name for name in s3_online_files if name.startswith(init_name)), None)
        
        track = info["tracking"]
        if match:
            sz = s3_online_files[match]['Size']
            track.update({
                "file_exists_online": True,
                "file_name": match,
                "file_size_mb_online": round(sz/(1024**2), 2)
            })
            if not track.get("is_done"): total_download_bytes += sz
        else:
            track["file_exists_online"] = False

    queue = {fid: info for fid, info in inventory.items() 
             if not info["tracking"].get("is_done") and info["tracking"].get("file_exists_online")}

    if not queue:
        print("✨ [SKIP] No files need downloading (All local or missing on S3).")
        return True

    total_q = len(queue)
    the_num_char = len(str(total_q))
    done = 0

    print("="*120)
    print(f"🚀 [START] Downloading {total_q} files ({round(total_download_bytes/(1024**2),2)} MB) | Threads: {threads}")
    print(f"{'PROGRESS':<10} | {'FID':<10} | {'S3 FILENAME':<75} | {'SIZE':<10} | {'STATUS'}")
    print("-" * 120)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(download_s3_item_worker, fid, info, s3_client): fid for fid, info in queue.items()}
        for future in as_completed(futures):
            fid, status, fname, fsize = future.result()
            with lock:
                done += 1
                prog_str = f"[{done:0{the_num_char}}/{total_q}]"
                
                if status in ["SUCCESS", "ALREADY_DONE"]:
                    inventory[fid] = update_one_item_inventory_download(inventory[fid])
                    checkpoint_counter += 1
                    color = "\033[92m" if status == "SUCCESS" else "\033[94m"
                    print(f"{prog_str:<10} | {fid:<10} | {fname:<75} | {fsize:>7} MB | {color}[{status}]\033[0m ✅")
                else:
                    print(f"{prog_str:<10} | {fid:<10} | {fname:<75} | {fsize:>7} MB | \033[91m[{status}]\033[0m ❌")
                
                if checkpoint_counter >= checkpoint_n:
                    plan_data = update_dict_plan_download(dict_plan=plan_data)
                    save_dict_plan_as_json_file(dict_plan=plan_data, path_json=str(path_json))
                    checkpoint_counter = 0

    plan_data = update_dict_plan_download(dict_plan=plan_data)
    save_dict_plan_as_json_file(dict_plan=plan_data, path_json=str(path_json))
    print("="*120 + "\n✅ Action 03 Finished.")
    return True

# ===================================================================
# MAIN DIAGNOSTIC (Unit Test)
# ===================================================================
if __name__ == "__main__":
    # Ajusta estos parámetros para tu prueba local
    test_params = {
        "sat_id": "19", 
        "product_id": "ABI-L2-LSTF", 
        "year": "2026", 
        "day": "003",
        "threads": 4,
        "checkpoint_n": 1
    }
    
    print("\n" + " LEGION-GOES: RUN PLAN DOWNLOAD DIAGNOSTIC ".center(80, "="))
    
    try:
        success = run_action(**test_params)
        if success:
            print("\n🏁 Process completed successfully.")
        else:
            print("\n⚠️ Process finished with warnings or failed to start.")
            
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ [FATAL ERROR]: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80 + "\n")
