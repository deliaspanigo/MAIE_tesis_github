# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act02/step02_update_dict_parts/update_dict03_inventory.py
# Version: 1.7.5 (Fixed: Absolute Physical Sync)
# =============================================================================
import os
from pathlib import Path  

def update_dict03_inventory(dict_plan: dict) -> dict:
    inventory = dict_plan.get('inventory', {})
    total = len(inventory)
    
    for i, (fid, info) in enumerate(inventory.items(), 1):
        inventory[fid] = update_one_item_inventory_download(info)
        if i % 100 == 0 or i == total:
            print(f"    ... audited {i}/{total} items")
            
    return dict_plan

def update_one_item_inventory_download(info: dict) -> dict:
    folder_abs = Path(info['folder_local']['path_absolute'])
    folder_rel = Path(info['folder_local']['path_relative'])
    
    info['folder_local']['folder_exists'] = folder_abs.exists()
    target_file_path = None

    if info['folder_local']['folder_exists']:
        init_name = info['file_local']['init_name']
        actual_files = list(folder_abs.glob(f"{init_name}*.nc"))
        if actual_files:
            target_file_path = actual_files[0]

    if target_file_path:
        # --- CASE: FILE EXISTS ---
        file_size_mb = round(target_file_path.stat().st_size / (1024 * 1024), 2)
        info['status'].update({'exists_local': True, 'is_done': True}) # <--- Confirmamos éxito
        info['file_local'].update({
            "file_name": target_file_path.name,
            "file_exists": True,
            "size_mb": file_size_mb,
            "path_absolute": str(target_file_path.resolve()),
            "path_relative": str(folder_rel / target_file_path.name)
        })
    else:
        # --- CASE: FILE MISSING (CRITICAL FIX) ---
        info['status'].update({'exists_local': False, 'is_done': False}) # <--- RESETEAMOS IS_DONE
        info['file_local'].update({
            "file_exists": False, 
            "file_name": None, 
            "size_mb": None
        })
    
    return info
