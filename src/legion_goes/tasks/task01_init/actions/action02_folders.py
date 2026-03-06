# =============================================================================
# FILE PATH: src/legion_goes/tasks/task01_init/actions/action02_folders.py
# Version: 1.0.0 (Folder Management Action)
# =============================================================================

import os
from legion_goes.SoT.goes_hardcoded_folders import LEGION_DATA_ROOT, GOES_FOLDERS

def create_folder_structure():
    """Verifica y crea la estructura de directorios necesaria."""
    
    print(f"[SYSTEM] Checking minimal folder structure environment...")
    
    for folder_key, folder_path in GOES_FOLDERS.items():
        # --- AQUÍ FILTRAMOS LA QUE NO QUIERES ---
        # Sustituye "NOMBRE_A_EXCLUIR" por el nombre exacto de la key en el SoT
        if folder_key == "NOMBRE_A_EXCLUIR":
            continue 
            
        full_path = os.path.join(LEGION_DATA_ROOT, folder_path)
        
        # Crear si no existe
        os.makedirs(full_path, exist_ok=True)
        
        print(f"  + Checking directory: {folder_key} -> OK")
    
    print(f"[SUCCESS] LEGION-GOES Environment ready for processing.\n")
