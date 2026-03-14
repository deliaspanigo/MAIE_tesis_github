# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action02/update_dict_plan_proc_single.py
# Version: 2.1.6 (Symmetry Architecture Fix)
# =============================================================================
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def update_dict_plan_proc_single(dict_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sincroniza el estado del disco con el inventario del Plan.
    Busca inputs (NC) y outputs (Science/Gallery/Meta).
    """
    from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict04_summary

    inventory = dict_plan.get("inventory", {})

    for fid, item in inventory.items():
        # --- 1. AUDIT INPUT (¿Está el NetCDF original?) ---
        # Basado en tu estructura: item["definition"]["input_info"]["hard"]
        in_info = item["definition"]["input_info"]
        folder_in = Path(in_info["hard"]["folder_path_absolute"])
        init_name = in_info["hard"]["init_name"]
        
        # Búsqueda real en disco
        found_files = list(folder_in.glob(f"{init_name}*")) if folder_in.exists() else []
        
        if found_files:
            actual_f = found_files[0]
            in_info["soft"] = {
                "file_name": actual_f.name,
                "file_path": str(actual_f.absolute()),
                "file_exists": True,
                "file_size": round(actual_f.stat().st_size / (1024**2), 2) # MB
            }
            item["tracking"]["is_ready_to_proc"] = True
        else:
            in_info["soft"]["file_exists"] = False
            item["tracking"]["is_ready_to_proc"] = False

        # --- 2. AUDIT OUTPUTS (¿Se generaron los resultados?) ---
        out_info = item["definition"]["output_info"]
        all_processing_done = True
        
        # Revisamos Pack01, Pack02 y Pack03 (si existe)
        for p_key in ["pack01", "pack02", "pack03"]:
            if p_key not in out_info: continue
            
            pack = out_info[p_key]
            # Usamos expected_files_paths que viene del execution_kwargs del Collector
            expected = pack["hard"].get("expected_files_paths", {})
            
            if not expected:
                all_processing_done = False
                continue
                
            pack_soft = {}
            pack_complete = True
            
            for file_id, path_str in expected.items():
                if path_str:
                    p_path = Path(path_str)
                    exists = p_path.exists()
                    pack_soft[file_id] = {
                        "exists": exists,
                        "size": round(p_path.stat().st_size / (1024**2), 3) if exists else 0
                    }
                    if not exists: pack_complete = False
                else:
                    pack_complete = False
            
            pack["soft"] = pack_soft
            if not pack_complete: all_processing_done = False

        # --- 3. TRACKING FINAL DEL ITEM ---
        item["tracking"]["is_done_proc"] = all_processing_done
        item["tracking"]["time_last_mod"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- 4. ACTUALIZACIÓN DEL SUMMARY ---
    # Esto es lo que hace que el 0.0% cambie a 100% o lo que corresponda
    dict_plan["summary"] = generate_dict04_summary.generate_dict(dict_proc_inventory=inventory)
    
    return dict_plan
