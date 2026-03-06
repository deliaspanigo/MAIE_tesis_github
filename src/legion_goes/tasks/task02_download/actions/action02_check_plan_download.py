# =============================================================================
# PATH: src/legion_goes/task/task02_download/actions/action02_check_plan_download.py
# Version: 0.8.3 (Atomic Design - English Version)
# =============================================================================

import json
from pathlib import Path
from datetime import datetime
from legion_goes.SoT.goes_sat import get_sat_info
from .fn01_file_name_plan_download import generate_plan_download_file_path

# --- 1. ATOMIC I/O ---

def load_dict_plan_file_json(path_plan: Path) -> dict:
    """Loads the download plan JSON file."""
    if not path_plan.exists(): 
        return None
    with open(path_plan, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_dict_plan_json(path_plan: Path, plan_data: dict):
    """Saves the download plan dictionary to a JSON file."""
    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=4)

# --- 2. ATOMIC ITEM PROCESSOR ---

def update_one_item_inventory_download(info: dict) -> dict:
    """
    Analyzes a single inventory item and updates its physical status in the dict.
    This is the minimum processing unit for both Checker and Downloader.
    """
    folder_abs = Path(info['folder_local']['path_absolute'])
    folder_rel = Path(info['folder_local']['path_relative'])
    
    info['folder_local']['folder_exists'] = folder_abs.exists()
    target_file_path = None

    if info['folder_local']['folder_exists']:
        init_name = info['file_local']['init_name']
        # Physical scan on Legion's disk
        actual_files = list(folder_abs.glob(f"{init_name}*.nc"))
        if actual_files:
            target_file_path = actual_files[0]

    if target_file_path:
        file_size_mb = round(target_file_path.stat().st_size / (1024 * 1024), 2)
        info['status'].update({'exists_local': True, 'is_done': True})
        info['file_local'].update({
            "file_name": target_file_path.name,
            "file_exists": True,
            "size_mb": file_size_mb,
            "path_absolute": str(target_file_path.resolve()),
            "path_relative": str(folder_rel / target_file_path.name)
        })
    else:
        info['status']['exists_local'] = False
        info['file_local'].update({
            "file_exists": False, 
            "file_name": None, 
            "size_mb": None,
            "path_absolute": None
        })
    
    return info

# --- 3. PURE LOGIC: DICT TRANSFORMATION ---

def update_dict_plan_check_inventory(plan_data: dict) -> dict:
    """Iterates through the entire inventory applying the single-item processor."""
    inventory = plan_data.get('download_inventory', {})
    total = len(inventory)
    
    for i, (fid, info) in enumerate(inventory.items(), 1):
        # Atomic update
        inventory[fid] = update_one_item_inventory_download(info)

        if i % 100 == 0 or i == total:
            print(f"    ... scanned {i}/{total} items")
            
    return plan_data

def update_dict_plan_check_summary(plan_data: dict) -> dict:
    """High-level analysis of the plan status."""
    inventory = plan_data.get('download_inventory', {})
    total_expected = plan_data['summary']['expected_total_files']
    
    found_count = sum(1 for item in inventory.values() if item['status'].get('is_done'))
    
    plan_data['summary'].update({
        'local_total_files': found_count,
        'is_done': (found_count == total_expected),
        'check_last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return plan_data

# --- 4. ORCHESTRATION ---

def update_dict_plan_check_all(plan_data: dict) -> dict:
    """Wraps inventory and summary updates in a single call."""
    plan_data = update_dict_plan_check_inventory(plan_data)
    plan_data = update_dict_plan_check_summary(plan_data)
    return plan_data # Corrected: now returns the modified data
    
def execute_task02_download_action02_check_plan(sat_id: str, year: int, day: int, product_id: str, output_folder_base: str):
    """Main entry point to check local integrity of a download plan."""
    str_day = str(day).zfill(3)
    str_year = str(year)
    
    try:
        sat_info = get_sat_info(sat_id)
        sat_label = f"GOES{sat_info['id']} - {sat_info['pos'].upper()}"
    except:
        sat_label = f"ID:{sat_id}"

    path_plan = generate_plan_download_file_path(
        year=str_year, day=str_day, sat_id=sat_id, 
        product_id=product_id, output_folder_base=output_folder_base
    )

    # Load Plan
    plan_data = load_dict_plan_file_json(path_plan)
    if not plan_data:
        print(f"\n⚠️ Error: No plan found at {path_plan}")
        return False

    print(f"\n🔍 [SCAN] Checking local integrity: {product_id} | {str_year}{str_day} ({sat_label})")

    # Transformation Chain
    plan_data = update_dict_plan_check_all(plan_data)
    
    # Save Progress
    save_dict_plan_json(path_plan, plan_data)

    summary = plan_data['summary']
    print(f"\n ✅ Scan finished: {summary['local_total_files']}/{summary['expected_total_files']} files found.")
    return True
