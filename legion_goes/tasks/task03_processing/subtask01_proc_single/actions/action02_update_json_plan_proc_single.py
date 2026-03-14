# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/action02_update_json_plan_proc_single.py
# Version: 2.4.0 (None-Status & Granular Tracking)
# =============================================================================
import os
import json
from pathlib import Path
from datetime import datetime

# --- ABSOLUTE IMPORTS ---
from legion_goes.code.python_sp.f99_common.load_dict_plan_from_json_file import load_dict_plan_from_json_file
from legion_goes.code.python_sp.f99_common.save_dict_plan_as_json_file import save_dict_plan_as_json_file
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.generate_plan_proc_single_json_file_path import generate_plan_proc_single_json_file_path
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict04_summary

def run_action(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01") -> bool:
    """
    Action 02: Escanea el disco basándose en los 3 Packs del plan.
    Convierte estados iniciales 'None' en 'True' o 'False'.
    """
    ctx = "[Action02 - Update]"
    
    # 1. Localizar el archivo JSON
    path_plan = generate_plan_proc_single_json_file_path(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )

    if not path_plan.exists():
        print(f"❌ {ctx} Error: Plan no encontrado en {path_plan}")
        return False

    # 2. Cargar el contenido
    plan_data = load_dict_plan_from_json_file(path_json=str(path_plan))
    if not plan_data: return False

    inventory = plan_data.get("inventory", {})
    print(f"\n🔍 {ctx} Auditando {len(inventory)} items...")

    # 3. BUCLE DE AUDITORÍA
    for fid, item in inventory.items():
        # --- A. AUDIT INPUT (Búsqueda del NetCDF descargado) ---
        in_hard = item["definition"]["input_info"]["hard"]
        in_folder = Path(in_hard["folder_path_absolute"])
        init_name = in_hard["init_name"]
        
        found_inputs = list(in_folder.glob(f"{init_name}*")) if in_folder.exists() else []
        
        if found_inputs:
            actual_file = found_inputs[0]
            item["definition"]["input_info"]["soft"].update({
                "file_name": actual_file.name,
                "file_path": str(actual_file.absolute()),
                "file_exists": True,
                "file_size_mb": round(actual_file.stat().st_size / (1024**2), 2)
            })
            item["tracking"]["is_ready_to_proc"] = True
        else:
            item["tracking"]["is_ready_to_proc"] = False

        # --- B. AUDIT OUTPUTS (Triple Pack con tus Listas Separadas) ---
        output_info = item["definition"]["output_info"]
        pack_results = {} 
        
        for p_id in ["pack01", "pack02", "pack03"]:
            pack = output_info.get(p_id)
            if not pack:
                item["tracking"][f"is_done_{p_id}"] = False
                pack_results[p_id] = False
                continue
            
            # Mapeo a tu nueva estructura soft: list_file_exists y list_file_size
            paths_map = pack["hard"].get("list_files_paths", {})
            exists_map = pack["soft"]["list_file_exists"]
            size_map = pack["soft"]["list_file_size"]
            
            p_complete = True
            
            for k, p_str in paths_map.items():
                # Filtro de seguridad para rutas (ignora configs como target_width)
                if isinstance(p_str, str) and ('.' in p_str or '/' in p_str):
                    p_path = Path(p_str)
                    if p_path.exists():
                        exists_map[k] = True
                        size_map[k] = round(p_path.stat().st_size/(1024**2), 3)
                    else:
                        # Aquí cambiamos None -> False explícitamente
                        exists_map[k] = False
                        size_map[k] = 0
                        p_complete = False
                else:
                    # No es una ruta auditale, no afecta al completion
                    continue
            
            # Guardamos el estado del pack individual
            item["tracking"][f"is_done_{p_id}"] = p_complete
            pack_results[p_id] = p_complete

        # --- C. UPDATE GLOBAL TRACKING ---
        # Solo es True si los 3 packs se verificaron como True
        item["tracking"]["is_done_proc"] = all(pack_results.values())
        item["tracking"]["time_last_mod"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. RECALCULAR SUMMARY (v.0.0.1)
    plan_data["summary"] = generate_dict04_summary.generate_dict(dict_proc_inventory=inventory)

    # 5. GUARDAR CAMBIOS
    save_dict_plan_as_json_file(dict_plan=plan_data, path_json=str(path_plan))

    # REPORTE DE CONSOLA
    s = plan_data["summary"]["status"]
    print(f"{'='*60}")
    print(f"📊 REPORTE FINAL: {s.get('progress_percentage')} de avance.")
    print(f"   Items Done: {s.get('files_completed')} / {s.get('total_files_in_scope')}")
    print(f"{'='*60}\n")

    return True

if __name__ == "__main__":
    params = {
        "sat_id": "19", 
        "product_id": "ABI-L2-LSTF", 
        "year": "2026", 
        "day": "003", 
        "fnp_tag": "fnp01"
    }
    run_action(**params)
