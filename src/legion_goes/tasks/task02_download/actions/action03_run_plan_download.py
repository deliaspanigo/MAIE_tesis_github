# =============================================================================
# PATH: src/legion_goes/task/task02_download/actions/action03_run_plan_download.py
# Version: 1.6.2 (UI Original Restaurada + Fix Metadata None)
# =============================================================================

import os
import boto3
import threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config

# Importing tools from Action 02
from .action02_check_plan_download import (
    load_dict_plan_file_json,
    save_dict_plan_json,
    update_one_item_inventory_download,
    update_dict_plan_check_all
)

# Thread Lock for synchronized dictionary and counter access
lock = threading.Lock()
checkpoint_counter = 0

# --- 1. ATOMIC WORKER: S3 TO TMP ---

def download_s3_item_worker(fid, info, s3_client):
    bucket = info["file_s3"]["bucket"]
    prefix = info["file_s3"]["prefix_hour"]
    init_name = info["file_s3"]["init_name"]
    
    try:
        # Usamos el nombre real si ya lo tenemos del Bulk Scan, si no, lo buscamos
        real_name = info["file_s3"].get("file_name")
        if not real_name:
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/{init_name}")
            if 'Contents' not in response:
                return fid, "404_NOT_FOUND"
            obj = response['Contents'][0]
            s3_full_key = obj['Key']
            s3_size_bytes = obj['Size']
            real_filename = s3_full_key.split('/')[-1]
        else:
            s3_full_key = f"{prefix}/{real_name}"
            # Convertimos MB a Bytes para validar
            s3_size_bytes = int(info["file_s3"]["size_mb"] * 1024 * 1024) if info["file_s3"]["size_mb"] else 0
            real_filename = real_name

        dest_folder = Path(info["folder_local"]["path_absolute"])
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        final_path = dest_folder / real_filename
        tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

        s3_client.download_file(bucket, s3_full_key, str(tmp_path))

        local_size_bytes = tmp_path.stat().st_size
        if abs(local_size_bytes - s3_size_bytes) < (0.1 * 1024 * 1024): # Margen de error por redondeo
            if final_path.exists(): os.remove(final_path)
            tmp_path.rename(final_path)
            return fid, "SUCCESS"
        else:
            if tmp_path.exists(): os.remove(tmp_path)
            return fid, f"SIZE_MISMATCH: {local_size_bytes} vs {s3_size_bytes}"

    except Exception as e:
        return fid, f"ERROR: {str(e)}"

# --- 2. CLEANER TOOLS ---

def cleanup_temporals(plan_data):
    print("🧹 [CLEANUP] Scanning for temporary files...")
    deleted_count = 0
    folders = {Path(item["folder_local"]["path_absolute"]) for item in plan_data["download_inventory"].values()}
    for folder in folders:
        if folder.exists():
            for tmp_file in folder.glob("*.tmp"):
                try:
                    tmp_file.unlink()
                    deleted_count += 1
                except: pass
    if deleted_count > 0:
        print(f"🗑️  Cleanup: {deleted_count} .tmp files removed.")

# --- 3. METADATA UPDATER ---

def update_inventory_item_with_s3_metadata(plan_data: dict, fid: str, s3_file_name: str, exists_online: bool, s3_file_size: any) -> dict:
    if "download_inventory" not in plan_data:
        return plan_data

    if fid in plan_data["download_inventory"]:
        item = plan_data["download_inventory"][fid]
        item["status"]["exists_online"] = exists_online
        item["file_s3"]["file_name"] = s3_file_name
        item["file_s3"]["file_exists"] = exists_online
        item["file_s3"]["size_mb"] = s3_file_size # Puede ser float o None
    
    return plan_data

# --- 4. DAILY REPORT ---

def display_daily_status_report(plan_data: dict):
    inventory = plan_data.get('download_inventory', {})
    # Colores
    C_RESET = "\033[0m"
    C_GREEN = "\033[92m"
    C_ORANGE = "\033[93m"
    C_CYAN = "\033[96m"
    C_RED = "\033[91m"
    C_WHITE = "\033[97m"

    hourly_stats = {f"{h:02d}": {"exp": 0, "s3": 0, "loc": 0} for h in range(24)}
    for info in inventory.values():
        h_str = str(info.get('hour', '00')).zfill(2)
        if h_str in hourly_stats:
            hourly_stats[h_str]["exp"] += 1
            if info.get("status", {}).get("exists_online"): hourly_stats[h_str]["s3"] += 1
            if info.get("status", {}).get("exists_local"): hourly_stats[h_str]["loc"] += 1

    width = 95
    print("\n" + "═" * width)
    print(f" 🕒 SYSTEM TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | UTC: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
    print(f" 📅 DAILY DOWNLOAD MONITOR (Legion Goes v.0.0.1)")
    print("═" * width)
    # Ajuste de cabecera para que coincida con las divisiones inferiores
    print(f"  HOUR  ║    EXP     │     S3     │   LOCAL    │    MISS    ║ STATUS")
    print("════════╬════════════╪════════════╪════════════╪════════════╬" + "═" * 35)

    for h in range(24):
        h_str = f"{h:02d}"
        s = hourly_stats[h_str]
        if s["exp"] == 0: continue
        miss = s["exp"] - s["loc"]
        
        # Lógica de Status con colores corregidos
        if s["loc"] == s["exp"]: 
            status = f"{C_GREEN}OK ✅{C_RESET}"
        elif s["s3"] == 0: 
            status = f"{C_CYAN}Not Available Yet{C_RESET}"
        elif s["s3"] == s["exp"]: 
            status = f"{C_WHITE}Available Complete{C_RESET}"
        else: 
            status = f"{C_ORANGE}Available Incomplete{C_RESET}"
        
        # El truco es usar format para asegurar que el ANSI no rompa el ancho
        miss_val = f"{C_RED}{miss:^10}{C_RESET}" if miss > 0 else f"{miss:^10}"
        
        print(f"   {h_str:^4} ║ {s['exp']:^10} │ {s['s3']:^10} │ {s['loc']:^10} │ {miss_val} ║ {status}")
    
    print("═" * width + "\n")

# --- 5. CORE ORCHESTRATION ---

def execute_task02_download_action03_run_download(path_plan: Path, threads=5, checkpoint_n=10):
    global checkpoint_counter
    checkpoint_counter = 0 
    
    plan_data = load_dict_plan_file_json(path_plan)
    if not plan_data: return False

    print(f"\n🔍 [PRE-CHECK] Synchronizing local inventory...")
    plan_data = update_dict_plan_check_all(plan_data)
    save_dict_plan_json(path_plan, plan_data)
    cleanup_temporals(plan_data)

    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket = plan_data['sat_prod_info']['bucket']
    prefix_day = f"{plan_data['sat_prod_info']['product_id']}/{plan_data['sat_prod_info']['year']}/{plan_data['sat_prod_info']['day']}/"

    print(f"🔍 [SCANNING] Fetching full day inventory from S3 bucket: {bucket}...")
    s3_online_files = {}
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix_day):
            if 'Contents' in page:
                for obj in page['Contents']:
                    filename = obj['Key'].split('/')[-1]
                    s3_online_files[filename] = obj
    except Exception as e:
        print(f"❌ Critical S3 Error: {e}"); return False

    inventory = plan_data["download_inventory"]
    online_available_count = 0
    total_download_bytes = 0
    
    for fid, info in inventory.items():
        init_name = info["file_s3"]["init_name"]
        match = next((name for name in s3_online_files if name.startswith(init_name)), None)
        
        if match:
            size_bytes = s3_online_files[match]['Size']
            size_mb = round(size_bytes / (1024 * 1024), 2)
            plan_data = update_inventory_item_with_s3_metadata(plan_data, fid, match, True, size_mb)
            if not info["status"].get("is_done"):
                online_available_count += 1
                total_download_bytes += size_bytes
        else:
            plan_data = update_inventory_item_with_s3_metadata(plan_data, fid, None, False, None)

    display_daily_status_report(plan_data)

    # --- SUMMARY CALCULATIONS ---
    total_planned = len(inventory)
    queue = {fid: info for fid, info in inventory.items() if not info["status"].get("is_done") and info["status"].get("exists_online")}
    local_count = total_planned - len({fid: info for fid, info in inventory.items() if not info["status"].get("is_done")})
    to_download_count = len(queue)
    weight_str = f"{round(total_download_bytes / (1024**2), 2)} MB" if total_download_bytes < (1024**3) else f"{round(total_download_bytes / (1024**3), 2)} GB"

    print("\n" + "="*60)
    print(f"{'📊 PRE-FLIGHT DOWNLOAD SUMMARY':^60}")
    print("="*60)
    print(f" { 'Category':<30} | { 'Value':<25} ")
    print("-" * 60)
    print(f" { 'Total Files Planned':<30} | { total_planned:<25} ")
    print(f" { 'Files Already Local':<30} | { local_count:<25} ")
    print(f" { 'Files Available Online':<30} | { f'{online_available_count} / {total_planned}':<25} ")
    print(f" { 'Files to Download Now':<30} | { to_download_count:<25} ")
    print(f" { 'Total Download Weight':<30} | { weight_str:<25} ")
    print("="*60)

    if to_download_count == 0:
        print("✨ [SKIP] Everything is local or not available yet.\n")
        return True

    # --- DOWNLOAD EXECUTION (TU UI ORIGINAL) ---
    downloaded_count = 0
    padding = len(str(to_download_count))
    print(f"🚀 [START] Downloading {to_download_count} files ({weight_str}) using {threads} threads.\n")
    
    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(download_s3_item_worker, fid, info, s3_client): fid for fid, info in queue.items()}
            for future in as_completed(futures):
                fid, status = future.result()
                with lock:
                    downloaded_count += 1
                    progress = f"{downloaded_count:0{padding}d}/{to_download_count:0{padding}d}"
                    status_tag = f"[\033[94mDownloading\033[0m]"
                    
                    if status == "SUCCESS":
                        inventory[fid] = update_one_item_inventory_download(inventory[fid])
                        checkpoint_counter += 1
                        file_name = inventory[fid]['file_local']['file_name']
                        file_size = f"({inventory[fid]['file_local']['size_mb']} MB)"
                        print(f"  [{progress}] {status_tag} {file_name:<80} {file_size:>12}  \033[92m[OK]\033[0m ✅")
                    else:
                        print(f"  [{progress}] {status_tag} {fid:<80} {'FAILED':>12}  \033[91m[FAIL]\033[0m ❌")

                    if checkpoint_counter >= checkpoint_n:
                        save_dict_plan_json(path_plan, plan_data)
                        checkpoint_counter = 0

    except KeyboardInterrupt:
        print("\n🛑 [STOP] Interrupted by user.")
    finally:
        save_dict_plan_json(path_plan, plan_data)
        plan_data = update_dict_plan_check_all(plan_data)
        print(f"\n📊 Final: {plan_data['summary']['local_total_files']}/{total_planned} files ready.")
        display_daily_status_report(plan_data)
    
    return True
