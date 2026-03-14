# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/action03_run_plan_proc_single.py
# Version: 3.6.0 (Feature: Immediate Audit on Success)
# =============================================================================
import os
from pathlib import Path

# --- ABSOLUTE IMPORTS ---
from legion_goes.code.python_sp.f99_common.load_dict_plan_from_json_file import load_dict_plan_from_json_file
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.generate_plan_proc_single_json_file_path import generate_plan_proc_single_json_file_path

# Importamos el Executor
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn02_run_executor.run_executor import run_executor

# Importamos la Action 02 para actualizar el diccionario tras cada éxito
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.action02_update_json_plan_proc_single import run_action as run_audit

def run_action(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01") -> bool:
    """
    Action 03: Despachador. 
    Tras cada ejecución exitosa, llama a la Action 02 para sincronizar el JSON.
    """
    ctx = "[Action03 - Dispatcher]"
    
    # 1. Localizar el plan JSON
    path_plan = generate_plan_proc_single_json_file_path(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )

    # 2. Cargar el contenido
    plan_data = load_dict_plan_from_json_file(path_json=str(path_plan))
    if not plan_data:
        print(f"❌ {ctx} Error: No se pudo cargar el plan.")
        return False

    inventory = plan_data.get("inventory", {})
    
    # 3. Filtrar pendientes
    pending_fids = [
        fid for fid, item in inventory.items() 
        if item["tracking"].get("is_ready_to_proc") and not item["tracking"].get("is_done_proc")
    ]

    if not pending_fids:
        print(f"☕ {ctx} Nada pendiente por procesar.")
        return True

    print(f"🚀 {ctx} Iniciando despacho de {len(pending_fids)} tareas...")

    # 4. BUCLE DE EJECUCIÓN + ACTUALIZACIÓN
    for i, fid in enumerate(pending_fids, 1):
        item = inventory[fid]
        nc_path = item["definition"]["input_info"]["soft"]["file_path"]

        print(f"\n📦 [{i}/{len(pending_fids)}] Ejecutando: {fid}")
        
        try:
            # EJECUCIÓN
            success = run_executor(nc_path=nc_path, fnp_tag=fnp_tag)
            
            if success:
                print(f"   ✅ Executor exitoso. Sincronizando Plan JSON...")
                # --- EL UPDATE CLAVE ---
                # Llamamos a la Action 02 para que verifique el disco y marque como DONE
                run_audit(sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag)
            else:
                print(f"   ⚠️  El Executor reportó fallos en {fid}. No se actualizó el estado.")
                
        except Exception as e:
            print(f"   ❌ [CRITICAL] Error en {fid}: {e}")
            continue

    print(f"\n✨ {ctx} Proceso terminado y JSON sincronizado.")
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
