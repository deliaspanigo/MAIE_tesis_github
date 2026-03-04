"""
Path: src/goes_processor/task/task02_download/actions/action02_check_plan_download.py
Version: 0.5.0 (Clean Parameter Mapping)
"""

import json
from pathlib import Path
from goes_processor.SoT.goes_sat import get_sat_info
from .fn01_file_name_plan_download import get_plan_download_file_path

def execute_action_check_plan(sat_id, product, year, day):
    """
    Sincroniza el JSON con la realidad del disco de la Legion.
    """
    # 1. Normalización de IDs (Importante para que no salga None)
    sat_data = get_sat_info(sat_id)
    real_id = str(sat_data["id"]).upper().replace("G", "")
    day_str = str(day).zfill(3)
    
    print(f"🔍 [SCAN] Checking local integrity: {product} | {year}{day_str} (G{real_id})")

    # 2. Localizar el Plan JSON
    path_plan = get_plan_download_file_path(year, day_str, real_id, product)
    
    if not path_plan.exists():
        print(f"⚠️  No plan found at {path_plan}")
        return False

    with open(path_plan, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)

    inventory = plan_data['inventory']
    found_count = 0

    # 3. Verificación Física
    for fid, info in inventory.items():
        # Construir la ruta donde DEBERÍA estar el archivo
        folder = Path(info['local_metadata']['folder_absolute'])
        init_name = info['s3_metadata']['init_name']
        
        # Buscamos si existe algún archivo que empiece con ese nombre
        # (Usamos glob para ignorar los segundos finales que pone NOAA)
        actual_files = list(folder.glob(f"{init_name}*.nc"))
        
        if actual_files:
            # Si existe, actualizamos el inventario
            inventory[fid]['status']['is_downloaded'] = True
            inventory[fid]['status']['file_name_final'] = actual_files[0].name
            inventory[fid]['status']['size_mb'] = round(actual_files[0].stat().st_size / (1024*1024), 2)
            found_count += 1
        else:
            # Si no está, nos aseguramos de que marque False
            inventory[fid]['status']['is_downloaded'] = False

    # 4. Guardar cambios en el JSON
    with open(path_plan, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=4)

    print(f" [+] Scan finished: {found_count} files found and verified on disk.")
    return True
