"""
Path: src/goes_processor/actions/a03_download/core01_download_from_s3/code01_download_s3_engine.py
Version: 1.0.8 (Clean Exit + Green Checks + Sys Control)
"""

import json
import boto3
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
from datetime import datetime

from goes_processor.SoT.goes_sat import get_goes_id_by_julian_date
from goes_processor.actions.a02_planning.core01_planner_download.fn01_file_name_plan_download import get_plan_download_file_path

json_lock = threading.Lock()

# --- COLORS ---
GREEN = "\033[92m"
RESET = "\033[0m"

# =============================================================================
# 1. ATOMIC DOWNLOAD TASK
# =============================================================================

def download_task(i, total, file_key, info, all_objects, bucket, path_plan, overwrite):
    try:
        search_pattern = info["file_local"]["init_name"]
        local_folder = Path(info["folder_local"]["path_absolute"])
        # --- Dynamic PADDING ---
        width = len(str(total))
        progress = f"[{i:0{width}d}/{total:0{width}d}]"
        # ---------------------------------------

        if not local_folder.exists():
            local_folder.mkdir(parents=True, exist_ok=True)

        session = boto3.session.Session()
        s3_client = session.client('s3', config=Config(signature_version=UNSIGNED))

        found_obj = next((obj for obj in all_objects if search_pattern in obj['Key']), None)
        if not found_obj:
            _update_json_v108(path_plan, file_key, exists_online=False)
            return {"status": "NOT_FOUND", "size_mb": 0}

        file_name = Path(found_obj['Key']).name
        s3_size = found_obj['Size']
        final_path = local_folder / file_name
        size_mb = round(s3_size / (1024 * 1024), 2)

        if final_path.exists() and not overwrite:
            if final_path.stat().st_size == s3_size:
                print(f"{progress} ✅ {GREEN}[ALREADY LOCAL]{RESET} {file_name}")
                _update_json_v108(path_plan, file_key, exists_online=True)
                return {"status": "SKIPPED", "size_mb": 0}

        prefix = "♻️  [OVERWRITE]" if (final_path.exists() and overwrite) else "📥 [DOWNLOADING]"
        print(f"{progress} {prefix} {file_name} ({size_mb} MB)...")
        
        receipt = _execute_transfer_v108(s3_client, bucket, found_obj['Key'], local_folder, s3_size)
        _update_json_v108(path_plan, file_key, exists_online=True, receipt=receipt)

        if "SUCCESS" in receipt["status"]:
            print(f"{progress} ✅ {GREEN}[SUCCESS]{RESET} {file_name} confirmed.")
        else:
            print(f"{progress} ❌ [FAILED] {file_name} | {receipt['status']}")
        
        return receipt
    except KeyboardInterrupt:
        return None

def _execute_transfer_v108(s3_client, bucket, remote_key, local_folder, s3_size):
    real_file_name = Path(remote_key).name
    final_path = local_folder / real_file_name
    temp_path = final_path.with_suffix(f".tmp.{threading.get_ident()}") # Evita colisión de hilos
    
    receipt = {"status": "PENDING", "file_name": real_file_name, "size_mb": round(s3_size/(1024*1024), 2),
               "t_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "t_end": None, "t_diff": None}

    try:
        t0 = time.time()
        s3_client.download_file(bucket, remote_key, str(temp_path))
        t1 = time.time()
        temp_path.rename(final_path)
        receipt.update({"status": "SUCCESS", "t_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "t_diff": round(t1 - t0, 2)})
    except Exception as e:
        receipt["status"] = f"ERROR: {str(e)}"
        if temp_path.exists(): temp_path.unlink()
    return receipt

def _update_json_v108(path_plan, file_key, exists_online, receipt=None):
    with json_lock:
        try:
            with open(path_plan, 'r') as f: plan = json.load(f)
            item = plan["download_inventory"][file_key]
            item["mini_summary"]["exists_online"] = exists_online
            if receipt and "SUCCESS" in receipt["status"]:
                item["mini_summary"].update({"is_done": True, "exists_local": True, "time_last_mod": receipt["t_end"]})
                item["file_local"].update({"exists_local": True, "file_size_mb": receipt["size_mb"]})
            with open(path_plan, 'w') as f: json.dump(plan, f, indent=4)
        except: pass

# =============================================================================
# 3. ORCHESTRATOR
# =============================================================================

def execute_s3_download(sat_position, product, year, day, threads, overwrite):
    try:
        sat_id = get_goes_id_by_julian_date(str(year), str(day), sat_position=sat_position)
        path_plan = get_plan_download_file_path(str(year), str(day), sat_id, sat_position, product)
        
        if not path_plan.exists(): return

        with open(path_plan, 'r') as f: plan_data = json.load(f)
        inventory, bucket, day_prefix = plan_data["download_inventory"], plan_data["sat_prod_info"]["bucket_name"], plan_data["sat_prod_info"]["prefix_day"]

        print("\n" + "🚀" * 30)
        print(f"🛰️  GOES-PROCESSOR DOWNLOADER | v.1.0.8")
        print(f"📦 PRODUCT: {product} | WORKERS: {threads}")
        print("🚀" * 30 + "\n")
        
        s3_main = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        all_objects = []
        paginator = s3_main.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=day_prefix):
            if 'Contents' in page: all_objects.extend(page['Contents'])

        results = []
        total = len(inventory)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            try:
                futures = [executor.submit(download_task, i, total, f_key, info, all_objects, bucket, path_plan, overwrite)
                           for i, (f_key, info) in enumerate(inventory.items(), 1)]
                
                for future in as_completed(futures):
                    res = future.result()
                    if res: results.append(res)
            except KeyboardInterrupt:
                print("\n⚠️  [INTERRUPTED] Stopping workers...")
                executor.shutdown(wait=False, cancel_futures=True)
                sys.exit(0)

        mb_total = sum(r["size_mb"] for r in results if r and r["status"] == "SUCCESS")
        files_ok = sum(1 for r in results if r and r["status"] in ["SUCCESS", "SKIPPED"])
        
        print(f"\n" + "═"*60)
        print(f"🏁 FINAL AUDIT SUMMARY | Julian Day {day}")
        print(f"═"*60)
        print(f"📊 Online found:     {len(all_objects)}")
        print(f"💾 Files on Disk:    {files_ok} / {total}")
        print(f"🛰️  Session Traffic:  {round(mb_total, 2)} MB")
        print(f"🏁 Process finished at: {datetime.now().strftime('%H:%M:%S')}")
        print("═"*60 + "\n")

    except Exception as e:
        print(f"🔥 FATAL ERROR: {e}")
        sys.exit(1)
