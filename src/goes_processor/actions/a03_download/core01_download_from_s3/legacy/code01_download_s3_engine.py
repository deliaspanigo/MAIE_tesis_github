"""
Path: src/goes_processor/actions/a03_download/core01_download_from_s3/code01_download_s3_engine.py
Description: Core engine for atomic S3 downloads, JSON synchronization, and real-time audit.
Version: 0.2.3 (Synced with SoT/goes_prod.py and SoT/goes_sat.py)
"""

import json
import boto3
import time
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path
from datetime import datetime

# --- FINAL CORRECTED IMPORTS (Based on your SoT directory) ---
from goes_processor.SoT.goes_sat import get_goes_id_by_julian_date
from goes_processor.SoT.goes_prod import SAVED_INFO_PROD_GOES 
from goes_processor.actions.a02_planning.core01_planner_download.fn01_file_name_plan_download import get_plan_download_file_path

# =============================================================================
# 1. OPERATIONAL ENGINE (Receipt Generator)
# =============================================================================

def download_single_file_s3(s3_client, bucket, remote_key, local_folder, s3_size):
    """
    Performs atomic download (using .tmp) and returns a receipt dictionary.
    """
    real_file_name = Path(remote_key).name
    final_path = Path(local_folder) / real_file_name
    temp_path = final_path.with_suffix(final_path.suffix + ".tmp")
    
    # Ensure local directory exists
    final_path.parent.mkdir(parents=True, exist_ok=True)

    receipt = {
        "status": "PENDING",
        "file_name": real_file_name,
        "size_mb": round(s3_size / (1024 * 1024), 2),
        "t_start": datetime.now().isoformat(),
        "t_end": None,
        "t_diff": None, 
        "path_absolute": str(final_path)
    }

    # Integrity check: Skip if file already exists with correct size
    if final_path.exists():
        if final_path.stat().st_size == s3_size:
            receipt["status"] = "SKIPPED_ALREADY_EXISTS"
            receipt["t_end"] = datetime.now().isoformat()
            return receipt

    # Atomic Download process
    try:
        t0 = time.time()
        s3_client.download_file(bucket, remote_key, str(temp_path))
        t1 = time.time()
        
        if temp_path.stat().st_size == s3_size:
            temp_path.rename(final_path)
            receipt["status"] = "SUCCESS"
            receipt["t_end"] = datetime.now().isoformat()
            receipt["t_diff"] = round(t1 - t0, 2)
        else:
            receipt["status"] = "ERROR_SIZE_MISMATCH"
            if temp_path.exists(): temp_path.unlink()
            
    except Exception as e:
        receipt["status"] = f"ERROR_FATAL: {str(e)}"
        if temp_path.exists(): temp_path.unlink()

    return receipt

# =============================================================================
# 2. SYNC LOGIC (Plan Updater)
# =============================================================================

def sync_receipt_to_plan(plan_dict, file_key, receipt):
    """
    Maps receipt data into the JSON plan structure to maintain state.
    """
    item = plan_dict["download_inventory"][file_key]
    is_ok = receipt["status"] in ["SUCCESS", "SKIPPED_ALREADY_EXISTS"]
    
    # Update Mini Summary
    item["mini_summary"]["is_done"] = is_ok
    item["mini_summary"]["exists_local"] = is_ok
    item["mini_summary"]["time_last_mod"] = receipt["t_end"]

    # Update S3 Info
    item["file_s3"]["file_name"] = receipt["file_name"]
    item["file_s3"]["file_size_mb"] = receipt["size_mb"]
    item["file_s3"]["dif_time_sec"] = receipt["t_diff"] 
    item["file_s3"]["exists_online"] = True
    
    # Update Local Info
    item["file_local"]["file_name"] = receipt["file_name"]
    item["file_local"]["path_absolute"] = receipt["path_absolute"]
    item["file_local"]["file_size_mb"] = receipt["size_mb"]
    item["file_local"]["exists_local"] = is_ok

    return plan_dict

# =============================================================================
# 3. MAIN ORCHESTRATOR (Audit Version v0.2.3)
# =============================================================================

def execute_s3_download(sat_position, product, year, day, threads):
    """
    Coordinates the download flow with step-by-step console feedback and audit summary.
    """
    # 1. Load Plan and SoT Metadata
    sat_id = get_goes_id_by_julian_date(str(year), str(day), sat_position=sat_position)
    path_plan = get_plan_download_file_path(str(year), str(day), sat_id, sat_position, product)

    # Metadata from SoT/goes_prod.py
    prod_metadata = SAVED_INFO_PROD_GOES.get(product, {})
    expected_count = prod_metadata.get("total_files_one_day", "Unknown")

    if not path_plan.exists():
        print(f"❌ Error: Download plan not found at: {path_plan}")
        return

    with open(path_plan, 'r') as f:
        plan_data = json.load(f)

    inventory = plan_data["download_inventory"]
    sat_prod_info = plan_data["sat_prod_info"]
    total_in_plan = len(inventory)
    
    # 2. S3 Client Setup
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket = sat_prod_info["bucket_name"]
    day_prefix = sat_prod_info["prefix_day"]

    print(f"🚀 Initializing download: {product} ({sat_position}) for {year}-{day}")
    print(f"📋 Theoretical expectation: {expected_count} files/day")
    print(f"📡 Scanning S3 server: {bucket}/{day_prefix}...")
    
    # Initial mass scan
    all_objects = []
    paginator = s3_client.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=day_prefix):
            if 'Contents' in page:
                all_objects.extend(page['Contents'])
    except Exception as e:
        print(f"❌ S3 Scanning Error: {e}")
        return

    online_count = len(all_objects)
    print(f"🔍 Found {online_count} files online. Starting process...\n")

    # 3. Processing Loop
    for i, (file_key, info) in enumerate(inventory.items(), 1):
        search_pattern = info["file_local"]["init_name"]
        local_folder = info["folder_local"]["path_absolute"]
        
        found_obj = next((obj for obj in all_objects if search_pattern in obj['Key']), None)
        progress = f"[{i:02d}/{total_in_plan:02d}]"

        if found_obj:
            file_name = Path(found_obj['Key']).name
            size_mb = round(found_obj['Size'] / (1024 * 1024), 2)
            
            # Step 1: Announce Target
            print(f"{progress} 🛰️  Target: {file_name} ({size_mb} MB)")
            
            # Execute download
            receipt = download_single_file_s3(s3_client, bucket, found_obj['Key'], local_folder, found_obj['Size'])
            
            # Sync and persist
            plan_data = sync_receipt_to_plan(plan_data, file_key, receipt)
            with open(path_plan, 'w') as f:
                json.dump(plan_data, f, indent=4)

            # Step 2: Feedback
            if receipt["status"] == "SUCCESS":
                print(f"       ✅ [FINISHED] Download complete in {receipt['t_diff']}s")
            elif receipt["status"] == "SKIPPED_ALREADY_EXISTS":
                print(f"       ✅ [SKIPPED]  File already exists locally.")
            elif "ERROR" in receipt["status"]:
                print(f"       ❌ [FAILED]   Reason: {receipt['status']}")
            
            print("-" * 55)
        else:
            print(f"{progress} ⚠️  [NOT FOUND] Pattern: {search_pattern}")

    # 4. FINAL AUDIT SUMMARY
    local_count = sum(1 for item in plan_data["download_inventory"].values() if item["mini_summary"]["exists_local"])

    print(f"\n" + "="*55)
    print(f"🏁 FINAL AUDIT SUMMARY | Day {day}")
    print(f"="*55)
    print(f"📈 Expected (SoT):  {expected_count}")
    print(f"🌐 Online (S3):    {online_count}")
    print(f"💻 Local (Legion): {local_count}")
    print(f"="*55)
    print(f"✨ Process finished. System in sync.\n")
