"""
Path: src/goes_processor/actions/a02_planning/core01_planner_download/code02_check_plan_download.py
Version: 0.1.9 (Dual-Layer Guard & CLI Bridge)
"""

# 1. CAPA DE SISTEMA
try:
    import json
    import glob
    from datetime import datetime
    from pathlib import Path
except ImportError as e:
    print(f"\n[SYSTEM LIB ERROR] - Critical libraries missing: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO
try:
    from goes_processor.SoT.goes_hardcoded_folders import get_my_path
    from goes_processor.SoT.goes_sat import get_goes_id_by_julian_date
    from .fn01_file_name_plan_download import get_plan_download_file_path
except ImportError as e:
    print(f"\n[PROJECT LIB ERROR] - Internal modules missing: {e}\n")
    raise SystemExit(1)

# =============================================================================
# CLI BRIDGE (Lo que llama cli02_check_plan.py)
# =============================================================================

def execute_check_plan(sat_position, product, year, day):
    """
    Bridge function to load the JSON plan, run the check, and save the updates.
    """
    ctx = "[BRIDGE - execute_check_plan]"
    try:
        # 1. Obtener la ruta del plan usando SoT
        sat_id = get_goes_id_by_julian_date(str(year), str(day), sat_position=sat_position)
        path_plan = get_plan_download_file_path(str(year), str(day), sat_id, sat_position, product)

        if not path_plan.exists():
            print(f"❌ Plan file not found at: {path_plan}")
            return

        # 2. Cargar el JSON
        with open(path_plan, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)

        # 3. Ejecutar tu lógica de chequeo (in-place)
        updated_plan = check_dict_download_plan_day(plan_data)

        # 4. Guardar los cambios en el JSON (ahora con los campos 'is_done' actualizados)
        with open(path_plan, 'w', encoding='utf-8') as f:
            json.dump(updated_plan, f, indent=4)
            
        print(f"✅ Plan updated on disk: {path_plan.name}")

    except Exception as e:
        print(f"💥 {ctx} Error: {e}")
        raise

# =============================================================================
# CORE LOGIC (Tu lógica original)
# =============================================================================

def check_dict_download_plan_day(plan: dict) -> dict:
    """
    Checks local existence of files in the download plan and updates 
    mini_summary and summary in-place.
    """
    ctx = "[Planning - check_dict_download_plan_day()]"
    
    try:
        if not isinstance(plan, dict):
            raise ValueError("The provided plan must be a dictionary.")

        data_raw_root = get_my_path("data_raw")
        inventory = plan.get("download_inventory", {})
        local_exists_count = 0
        total_size_mb = 0.0
        latest_mod_time = None

        sat_prod = plan.get("sat_prod_info", {})
        product = sat_prod.get("product_id", "unknown")
        date_j = sat_prod.get("date_julian", "unknown")

        print(f"🔍 Checking local integrity: {product} | {date_j}")

        for file_key, item in inventory.items():
            found_path = None

            # --- ESTRATEGIA 1: Ruta absoluta ---
            abs_path_str = item["file_local"].get("path_absolute")
            if abs_path_str:
                expected_path = Path(abs_path_str)
                if expected_path.exists() and expected_path.is_file():
                    found_path = expected_path

            # --- ESTRATEGIA 2: Fallback por Regex ---
            if found_path is None:
                s3_info = item.get("file_s3", {})
                regex = s3_info.get("regex")
                prefix = s3_info.get("prefix")
                
                if regex and prefix:
                    bucket = s3_info.get("bucket", "")
                    full_pattern = data_raw_root / bucket / prefix / regex
                    candidates = glob.glob(str(full_pattern))
                    valid_candidates = [Path(p) for p in candidates if Path(p).is_file()]
                    if valid_candidates:
                        found_path = max(valid_candidates, key=lambda p: p.stat().st_mtime)

            # --- ACTUALIZACIÓN ---
            if found_path:
                stat = found_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                size_mb = round(stat.st_size / (1024 * 1024), 3)
                
                item["mini_summary"]["is_done"] = True
                item["mini_summary"]["time_last_mod"] = mtime.strftime("%Y-%m-%d %H:%M:%S")
                item["file_local"]["file_exists_local"] = True
                item["file_local"]["file_size_mb_local"] = size_mb
                item["file_local"]["path_absolute"] = str(found_path.resolve())
                
                try:
                    item["file_local"]["path_relative"] = str(found_path.relative_to(data_raw_root))
                except ValueError:
                    item["file_local"]["path_relative"] = found_path.name
                
                item["folder_local"]["folder_exists_local"] = True
                local_exists_count += 1
                total_size_mb += size_mb
                if latest_mod_time is None or mtime > latest_mod_time:
                    latest_mod_time = mtime
            else:
                item["mini_summary"]["is_done"] = False
                item["file_local"]["file_exists_local"] = False

        # --- SUMMARY GENERAL ---
        total_items = len(inventory) if inventory else 1
        plan["summary"]["is_done"] = (local_exists_count == total_items)
        plan["summary"]["total_files_ready"] = local_exists_count
        plan["summary"]["total_size_mb"] = round(total_size_mb, 2)
        
        if latest_mod_time:
            plan["summary"]["time_last_mod"] = latest_mod_time.strftime("%Y-%m-%d %H:%M:%S")

        print(f" [+] Check complete: {local_exists_count}/{total_items} files found.")
        return plan

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: Error during plan check: {e}\n") from None
