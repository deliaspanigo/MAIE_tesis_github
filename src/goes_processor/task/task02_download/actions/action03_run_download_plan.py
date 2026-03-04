"""
Path: src/goes_processor/task/task02_download/actions/action03_run_download_plan.py
Version: 1.3.1 (Color Verbose Edition)
"""

import json
import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config

from .fn01_file_name_plan_download import get_plan_download_file_path

# --- CONSTANTES DE COLOR ANSI ---
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
CHECK = "✔"

def _fast_s3_download(fid, s3_info, local_info):
    """
    Worker: Descarga y devuelve metadatos para el log (nombre y peso).
    """
    try:
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        bucket = s3_info["bucket"]
        prefix = s3_info["prefix_hour"]
        init_name = s3_info["init_name"]

        # 1. Resolver nombre real y obtener metadatos (size)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/{init_name}")
        if 'Contents' not in response:
            return fid, "404_NOT_FOUND", None, 0

        obj = response['Contents'][0]
        s3_full_key = obj['Key']
        real_filename = s3_full_key.split('/')[-1]
        size_mb = round(obj['Size'] / (1024 * 1024), 2)
        
        target_path = Path(local_info["path_absolute"]) / real_filename
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Descarga física
        s3.download_file(bucket, s3_full_key, str(target_path))
        return fid, "SUCCESS", real_filename, size_mb
    except Exception:
        return fid, "ERROR", None, 0

def execute_action_run_download(sat_pos, year, day, product_id, threads, overwrite):
    path_plan = get_plan_download_file_path(str(year), str(day).zfill(3), sat_pos, product_id)
    
    if not path_plan.exists():
        print(f"  {RED}❌ Error: No existe el plan en {path_plan}{RESET}")
        return False

    with open(path_plan, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)

    inventory = plan_data["download_inventory"]
    summary = plan_data["summary"]
    total_expected = summary["total_files_expected"]
    max_digits = len(str(total_expected))
    
    files_done = sum(1 for f in inventory.values() if f["mini_summary"].get("is_done", False))
    print(f"\n📊 {BOLD}[STATUS]{RESET} {product_id}: {files_done}/{total_expected} archivos verificados.")

    if overwrite:
        queue = {fid: fdata for fid, fdata in inventory.items()}
    else:
        queue = {fid: fdata for fid, fdata in inventory.items() if not fdata["mini_summary"].get("is_done", False)}

    total_queue = len(queue)
    if total_queue == 0:
        print(f"  {GREEN}✨ {product_id}: All files already present (100%). Nothing to do.{RESET}")
        return True

    print(f"🚀 {BOLD}[START]{RESET} Iniciando descarga de {total_queue} archivos faltantes...")

    results = {"SUCCESS": 0, "ERROR": 0, "404_NOT_FOUND": 0}
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(_fast_s3_download, fid, fdata["file_s3"], fdata["folder_local"]): fid 
            for fid, fdata in queue.items()
        }

        processed = 0
        for future in as_completed(futures):
            processed += 1
            fid, status, filename, size = future.result()
            
            key_status = status if "ERROR" not in status else "ERROR"
            results[key_status] += 1
            
            # Formatear contador con ceros a la izquierda
            count_str = str(processed).zfill(max_digits)
            total_str = str(total_queue).zfill(max_digits)

            if status == "SUCCESS":
                inventory[fid]["mini_summary"]["is_done"] = True
                # --- LOG CON COLOR VERDE Y CHECK ---
                success_tag = f"{GREEN}{CHECK} [SUCCESS]{RESET}"
                print(f"  [{count_str}/{total_str}] {success_tag} {filename} ({size} MB)")
            else:
                error_tag = f"{RED}✖ [{status}]{RESET}"
                print(f"  [{count_str}/{total_str}] {error_tag} {fid}")

    final_done = sum(1 for f in inventory.values() if f["mini_summary"]["is_done"])
    summary["total_files_done"] = final_done
    
    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=4)

    print(f"\n🏁 {BOLD}[FINISHED]{RESET} {product_id}: {results}")
    print(f"📈 Estado final: {GREEN}{final_done}/{total_expected}{RESET} archivos listos.\n")
    
    return True
