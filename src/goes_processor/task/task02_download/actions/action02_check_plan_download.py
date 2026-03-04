"""
Path: src/goes_processor/task/task02_download/actions/action02_check_plan_download.py
Version: 0.3.9 (Progress Feedback Edition)
"""

import json
from pathlib import Path
from datetime import datetime
from .fn01_file_name_plan_download import get_plan_download_file_path

def execute_action_check_plan(sat_pos: str, year: int, day: int, product_id: str):
    ctx = "[Action02 - CheckPlan]"
    str_day = str(day).zfill(3)
    str_year = str(year)
    
    path_plan = get_plan_download_file_path(str_year, str_day, sat_pos, product_id)
    
    if not path_plan.exists():
        print(f"⚠️ {ctx} No plan found at {path_plan}")
        return False

    with open(path_plan, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)

    inventory = plan_data.get('download_inventory', {})
    total_expected = plan_data['summary']['total_files_expected']
    found_count = 0

    print(f"🔍 [SCAN] Checking local integrity: {product_id} | {str_year}{str_day} ({sat_pos.upper()})")

    for i, (fid, info) in enumerate(inventory.items(), 1):
        folder_abs = Path(info['folder_local']['path_absolute'])
        folder_rel = Path(info['folder_local']['path_relative'])
        
        info['folder_local']['folder_exists'] = folder_abs.exists()
        target_file_path = None

        if info['folder_local']['folder_exists']:
            # Prioridad 1: Nombre exacto de S3 (si ya se consultó)
            s3_filename = info['file_s3'].get('file_name')
            if s3_filename:
                potential_path = folder_abs / s3_filename
                if potential_path.exists():
                    target_file_path = potential_path

            # Prioridad 2: Búsqueda por patrón (init_name)
            if not target_file_path:
                init_name = info['file_local']['init_name']
                # Glob busca cualquier archivo que empiece por el prefijo (ej. OR_ABI-L2-LSTF-M6_G19_s2026...)
                actual_files = list(folder_abs.glob(f"{init_name}*.nc"))
                if actual_files:
                    target_file_path = actual_files[0]

        # Actualización de metadatos
        if target_file_path:
            file_size_mb = round(target_file_path.stat().st_size / (1024 * 1024), 2)
            info['mini_summary'].update({'exists_local': True, 'is_done': True})
            info['file_local'].update({
                "file_name": target_file_path.name,
                "file_exists": True,
                "size_mb": file_size_mb,
                "path_absolute": str(target_file_path.resolve()),
                "path_relative": str(folder_rel / target_file_path.name)
            })
            found_count += 1
        else:
            info['mini_summary']['exists_local'] = False
            # No forzamos is_done = False porque podría estar en S3 pero no local
            info['file_local'].update({
                "file_exists": False,
                "file_name": None,
                "size_mb": None
            })

        # Feedback de progreso para el usuario
        if i % 20 == 0 or i == total_expected:
            print(f"   ... scanned {i}/{total_expected} items")

    # Actualizar cabecera del JSON
    plan_data['summary'].update({
        'total_files_done': found_count,
        'is_done': (found_count == total_expected),
        'timestamp_file_last_mod': datetime.now().isoformat()
    })

    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=4)

    print(f" ✅ Scan finished: {found_count}/{total_expected} files found on disk.")
    return True
