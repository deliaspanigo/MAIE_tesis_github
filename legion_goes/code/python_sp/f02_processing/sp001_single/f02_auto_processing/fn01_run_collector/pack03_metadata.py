# =============================================================================
# Path: legion_goes/code/python_sp/f02_processing/sp001_single/f02_auto_processing/fn01_run_collector/pack03_metadata.py
# Version: 1.1.0 (Dynamic Schema Sync)
# Description: Logic for process auditing. Exports its own schema for the Plan.
# =============================================================================

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# IMPORTACIÓN CENTRALIZADA
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single

# --- CONTRATO DE SALIDA (Escalable) ---
dict_output_schema = {
    "meta_json": "meta.json"
}

def pack03_metadata(
    sat_id: str,
    product_id: str, 
    year: int,
    day: int,
    s_timestamp_short: str,
    fnp_tag: str
) -> Optional[Dict[str, Any]]:
    """
    Ensambla el 'BAG' para la generación de metadatos y auditoría.
    """
    # 1. Resolver carpeta de salida
    str_output_folder_abs = get_folder_full_path_proc_single(
        sat_id=sat_id,
        product_id=product_id,
        year=year,
        day=day,
        s_timestamp_short=s_timestamp_short,
        fnp_tag=fnp_tag
    )

    if not str_output_folder_abs:
        return None

    # 2. Generar rutas absolutas para el Auditor (Action 02)
    dict_output_file_path = {
        key: str(Path(str_output_folder_abs) / filename)
        for key, filename in dict_output_schema.items()
    }

    # 3. Ensamblar el BAG siguiendo el nuevo estándar
    bag = {
        "fnp_python_code": generate_process_metadata_json,
        "execution_kwargs": {
            "output_folder": str_output_folder_abs,
            "json_filename": dict_output_schema["meta_json"] # Dinámico
        },
        "meta": {
            "task_name": "Metadata & Audit Generation",
            "output_folder": str_output_folder_abs,
            "dict_output_file_name": dict_output_schema # Ahora presente en Pack 03
        },
        "execution_kwargs_audit": dict_output_file_path # Mapeo directo para el JSON
    }

    return bag

# =============================================================================
# CORE LOGIC
# =============================================================================

def generate_process_metadata_json(
    output_folder: str, 
    start_time: float, 
    json_filename: str = "meta.json"
) -> bool:
    """
    Audita la carpeta, calcula duraciones y guarda un reporte JSON.
    """
    try:
        folder = Path(output_folder)
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        # Auditoría de disco para el reporte interno
        files_found = sorted([f.name for f in folder.iterdir() if f.is_file()])
        
        if json_filename not in files_found:
            files_found.append(json_filename)
            files_found.sort()

        meta_data = {
            "execution_summary": {
                "start_iso": datetime.fromtimestamp(start_time).isoformat(),
                "end_iso": datetime.fromtimestamp(end_time).isoformat(),
                "duration_seconds": duration,
                "status": "completed"
            },
            "artifacts": {
                "count": len(files_found),
                "file_list": files_found
            },
            "environment": {
                "folder_path": str(folder.absolute())
            }
        }
        
        json_path = folder / json_filename
        with open(json_path, 'w') as f:
            json.dump(meta_data, f, indent=4)
            
        print(f"      📝 [METADATA] Audit completed. {len(files_found)} files registered.")
        return True

    except Exception as e:
        print(f"      ❌ [METADATA ERROR] {e}")
        return False
