import json
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pathlib import Path

try:
    from goes_processor.SoT.goes_sat import get_goes_id_by_julian_date
    from goes_processor.actions.a02_planning.core01_planner_download.fn01_file_name_plan_download import get_plan_download_file_path
except ImportError as e:
    print(f"❌ Import Error: {e}")

def execute_s3_download(sat_position, product, year, day, threads):
    ctx = "[DOWNLOAD ENGINE]"
    
    # 1. Cargar el Plan
    sat_id = get_goes_id_by_julian_date(str(year), str(day), sat_position=sat_position)
    path_plan = get_plan_download_file_path(str(year), str(day), sat_id, sat_position, product)

    if not path_plan.exists():
        print(f"❌ Plan not found: {path_plan.name}")
        return

    with open(path_plan, 'r') as f:
        plan_data = json.load(f)

    inventory = plan_data.get("download_inventory", {})
    total_files = len(inventory)
    
    # 2. Cliente S3
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    print(f"📦 Plan loaded: {total_files} files to process.")
    print(f"📡 Verifying integrity and downloading from S3...\n")

    for i, (key, info) in enumerate(inventory.items(), 1):
        s3_info = info["file_s3"]
        local_info = info["file_local"]
        
        bucket = s3_info["bucket"]
        prefix = s3_info["prefix"]
        search_pattern = local_info["file_name_expected"].replace(".nc", "")

        try:
            # Buscar el archivo real en S3 para obtener su peso oficial
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            found_obj = None
            if 'Contents' in response:
                for obj in response['Contents']:
                    if search_pattern in obj['Key']:
                        found_obj = obj
                        break

            if found_obj:
                remote_key = found_obj['Key']
                file_name = Path(remote_key).name
                s3_size_bytes = found_obj.get('Size', 0)
                s3_size_mb = s3_size_bytes / (1024 * 1024)
                
                local_path = Path(local_info["path_absolute"]).parent / file_name
                local_path.parent.mkdir(parents=True, exist_ok=True)

                progress_prefix = f"[{i:02d}/{total_files:02d}]"
                
                # --- VERIFICACIÓN DE INTEGRIDAD LOCAL ---
                if local_path.exists():
                    local_size_bytes = local_path.stat().st_size
                    
                    if local_size_bytes == s3_size_bytes:
                        print(f"{progress_prefix} ✅ [OK] Already exists & Integrity verified: {file_name} ({s3_size_mb:.2f} MB)")
                        continue
                    else:
                        print(f"{progress_prefix} ⚠️ [CORRUPT] Size mismatch (Local: {local_size_bytes} vs S3: {s3_size_bytes}). Redownloading...")
                        local_path.unlink() # Borrar archivo corrupto

                # --- DESCARGA ---
                print(f"{progress_prefix} 📥 [DOWNLOADING] {file_name} | Size: {s3_size_mb:.2f} MB")
                s3_client.download_file(bucket, remote_key, str(local_path))
            else:
                print(f"[{i:02d}/{total_files:02d}] ❌ [NOT FOUND] Pattern {search_pattern} in S3")

        except Exception as e:
            print(f"[{i:02d}/{total_files:02d}] 💥 Error: {e}")

    print(f"\n✅ All tasks finished. Check your 'data_raw' folder.")
