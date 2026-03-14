# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act02/step02_update_dict_parts/update_dict03_inventory.py
# Version: 1.2.0 (Sync with Action 03 Download & Schema v.1.7.x)
# =============================================================================

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def update_dict03_inventory(dict_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audits the entire download inventory.
    Iterates through all items and checks if they exist on local disk.
    """
    inventory = dict_plan.get('inventory', {})
    total = len(inventory)
    
    if total == 0:
        return dict_plan

    for fid, info in inventory.items():
        inventory[fid] = update_one_item_inventory_download(info)
        
    return dict_plan

def update_one_item_inventory_download(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    CORE FUNCTION: Audits a single download item.
    Checks:
    1. If the file exists in the absolute path.
    2. If the size matches the expected size from S3 (within margin).
    """
    definition = info.get('definition', {})
    tracking = info.get('tracking', {})
    
    # Acceso a rutas (Ajustado a estructura con rama 'hard')
    local_info = definition.get('local_folder_info', {})
    folder_path = local_info.get('hard', {}).get('folder_path_absolute', '')
    
    # Si la estructura vieja no tiene 'hard', intentamos el acceso directo (fallback)
    if not folder_path:
        folder_path = local_info.get('folder_path_absolute', '')
        
    file_name = tracking.get('file_name', '')
    expected_size_mb = tracking.get('file_size_mb_online', 0)
    
    if not folder_path or not file_name:
        tracking['is_done'] = False
        return info

    path_abs = Path(folder_path) / file_name
    
    # --- PHYSICAL DISK AUDIT ---
    if path_abs.exists():
        current_size_bytes = path_abs.stat().st_size
        current_size_mb = round(current_size_bytes / (1024**2), 2)
        
        # Guardamos el tamaño local detectado
        tracking['file_size_mb_local'] = current_size_mb
        
        # Verificación de integridad básica:
        # Se marca como DONE si el archivo existe y el tamaño no difiere 
        # más de 0.5 MB de lo que reporta S3.
        if abs(current_size_mb - expected_size_mb) < 0.5:
            tracking['is_done'] = True
        else:
            # Si el tamaño es muy diferente, probablemente está corrupto o incompleto
            tracking['is_done'] = False
    else:
        tracking['is_done'] = False
        tracking['file_size_mb_local'] = 0

    # Timestamp de la auditoría
    tracking['time_last_mod'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return info

# =============================================================================
# MAIN DIAGNOSTIC (Unit Test)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: UPDATE DOWNLOAD INVENTORY ".center(80, "="))
    
    # Mock de un ítem de descarga
    mock_item = {
        "definition": {
            "local_folder_info": {
                "hard": {"folder_path_absolute": "/tmp/legion_test"}
            }
        },
        "tracking": {
            "file_name": "test_goes.nc",
            "file_size_mb_online": 10.5,
            "is_done": False
        }
    }
    
    # Setup físico
    Path("/tmp/legion_test").mkdir(parents=True, exist_ok=True)
    test_file = Path("/tmp/legion_test/test_goes.nc")
    
    # Simular archivo con tamaño correcto (10.5 MB aprox)
    with open(test_file, "wb") as f:
        f.write(os.urandom(int(10.5 * 1024 * 1024)))
        
    print("🚀 Auditing mock item...")
    result = update_one_item_inventory_download(mock_item)
    
    print(f"\n✅ Result:")
    print(f"   - File: {result['tracking']['file_name']}")
    print(f"   - Is Done? {result['tracking']['is_done']}")
    print(f"   - Local Size: {result['tracking']['file_size_mb_local']} MB")
    
    # Limpieza
    test_file.unlink()
    print("\n" + "=" * 80 + "\n")
