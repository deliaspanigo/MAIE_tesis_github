# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action02/step02_update_dict_parts/update_dict03_inventory.py
# Version: 1.8.9 (Sequential Independence & Path Auto-Correction)
# =============================================================================

import json
from pathlib import Path
from datetime import datetime

def update_block_01_input(info: dict) -> bool:
    """BLOQUE 1: Independiente - Actualiza info del archivo de entrada .nc"""
    input_soft = info['definition']['input_info']['soft']
    input_hard = info['definition']['input_info']['hard']
    
    folder_in = Path(input_hard.get('folder_path_absolute', ''))
    init_name = input_hard.get('init_name', '')
    
    exists = False
    if folder_in.exists() and init_name:
        matches = list(folder_in.glob(f"{init_name}*"))
        if matches:
            actual_file = matches[0]
            input_soft.update({
                "file_name": actual_file.name,
                "file_path": str(actual_file.resolve()),
                "file_size": f"{round(actual_file.stat().st_size / (1024**2), 2)} MB",
                "file_exists": True
            })
            exists = True
    
    if not exists:
        input_soft["file_exists"] = False
        
    return exists

def update_block_02_output(info: dict) -> bool:
    """BLOQUE 2: Independiente - Actualiza info de los productos generados"""
    output_info = info['definition']['output_info']
    all_packs_done = True
    
    for pack_id, pack_data in output_info.items():
        p_hard = pack_data['hard']
        p_soft = pack_data['soft']
        
        # 1. Validar carpeta (con corrección si la ruta del JSON está mal cortada)
        folder_path = Path(p_hard.get('output_folder_absolute', ''))
        
        # Si la carpeta del JSON no existe, intentamos buscarla si termina en 'fnp01'
        if not folder_path.exists():
            parent = folder_path.parent
            if parent.exists():
                # Buscamos una carpeta que empiece igual (para arreglar lo de los ceros faltantes)
                matches = list(parent.glob(f"{folder_path.name}*"))
                if matches: folder_path = matches[0]

        p_soft['check_output_folder_absolute_exists'] = folder_path.exists()
        
        # 2. Validar Archivos
        pack_complete = True
        expected_paths = p_hard.get('expected_files_paths', {})
        files_status = p_soft.get('check_exists', {})
        
        for f_key, f_path in expected_paths.items():
            if not f_path: continue
            
            # Intentamos la ruta directa, si falla, buscamos el nombre en la carpeta corregida
            file_obj = Path(f_path)
            if not file_obj.exists() and folder_path.exists():
                file_obj = folder_path / file_obj.name # Re-intentar con la carpeta física real
            
            exists = file_obj.exists()
            
            if f_key not in files_status: files_status[f_key] = {}
            
            files_status[f_key]["exists"] = exists
            files_status[f_key]["file_size_mb"] = round(file_obj.stat().st_size / (1024**2), 3) if exists else 0.0
            
            if not exists: pack_complete = False
            
        if not pack_complete: all_packs_done = False
            
    return all_packs_done

def update_one_item_inventory_proc_single(info: dict) -> dict:
    """Ejecución lineal de los bloques de update."""
    
    # Ejecución Bloque 1
    is_ready = update_block_01_input(info)
    
    # Ejecución Bloque 2
    is_done = update_block_02_output(info)
    
    # Bloque 3: Tracking (Independiente)
    info['tracking']['is_ready_to_proc'] = is_ready
    info['tracking']['is_done_proc'] = is_done
    info['tracking']['time_last_mod'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return info

def update_dict03_inventory(dict_plan: dict) -> dict:
    inventory = dict_plan.get('inventory', {})
    for fid in inventory:
        inventory[fid] = update_one_item_inventory_proc_single(inventory[fid])
    return dict_plan
