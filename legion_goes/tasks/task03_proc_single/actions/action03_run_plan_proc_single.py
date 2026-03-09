# =============================================================================
# FILE PATH: src/legion_goes/tasks/task03_proc_single/actions/action03_run_plan_proc_single.py
# Version: 1.9.5 (Fixed Mapping & Path Extraction)
# =============================================================================

import json
import time
import importlib
import traceback
from pathlib import Path



def run_action03_run_plan_proc_single(path_plan_json, overwrite=False):
    """
    Legion Execution Engine.
    Lee el plan y ejecuta el executor de cada FNP.
    """
    

    
    ctx = "[Action 03 - Run Plan]"
    path_p = Path(path_plan_json)

    if not path_p.exists():
        print(f"❌ {ctx} No se encontró el plan: {path_plan_json}")
        return False

    with open(path_p, 'r') as f:
        plan = json.load(f)

    # 1. EXTRACCIÓN DE DATOS (Basado en tu estructura real)
    inventory = plan.get('proc_inventory', {})
    self_info = plan.get('self_info', {})
    fnp_tag = self_info.get('fnp_tag', 'fnp01')
    
    # IMPORTANTE: El Product ID viene del nombre del archivo si no está en sat_prod_info
    # Basado en tu JSON, asumimos ABI-L2-MCMIPF por defecto
    product_id = "ABI-L2-MCMIPF" 
    
    # 2. FILTRADO (Sincronizado con 'is_processed')
    items_to_proc = {}
    for fid, data in inventory.items():
        status = data.get('status', {})
        # Usamos 'is_processed' que es lo que viene en tu JSON
        already_done = status.get('is_processed', False)
        
        if overwrite or not already_done:
            items_to_proc[fid] = data

    total_to_run = len(items_to_proc)
    print(f"\n{ctx} 🌀 Engine Ready | FNP: {fnp_tag} | Escenas a procesar: {total_to_run}")

    if total_to_run == 0:
        print(f"✅ {ctx} Nada que procesar (Todo 'is_processed: true').")
        return True

    # 3. IMPORTACIÓN DINÁMICA
    prod_clean = product_id.replace("-", "_")
    fnp_folder = f"{prod_clean}_SP_single_{fnp_tag}"
    module_path = f"legion_goes.tasks.task03_proc_single.actions.fnp.{fnp_folder}.fn02_executor"
    
    try:
        mod = importlib.import_module(module_path)
        execute_task = getattr(mod, 'run_executor')
    except Exception as e:
        print(f"❌ {ctx} Error cargando motor {module_path}: {e}")
        return False

    # 4. BUCLE DE PROCESAMIENTO
    count = 0
    start_job = time.time()
    width = len(str(total_to_run))

    for fid, info in items_to_proc.items():
        count += 1
        
        # Mapeo de rutas
        nc_in = info['ref_input']['path_absolute']
        ref_out = info['ref_output']
        
        # --- APLANAR OUTPUTS ---
        # Convertimos el diccionario de objetos en diccionario de strings (paths)
        dict_out_flat = {}
        for out_key, out_val in ref_out.get('outputs', {}).items():
            dict_out_flat[out_key] = out_val['path_absolute']
        
        # La galería en tu JSON está dentro de outputs, así que ya se incluyó arriba.
        # Pero por si acaso, verificamos si está fuera:
        if 'gallery' in ref_out and isinstance(ref_out['gallery'], str):
             dict_out_flat['gallery'] = ref_out['gallery']

        print(f"\n🚀 [{str(count).zfill(width)}/{total_to_run}] Escena: {fid}")
        
        try:
            start_scene = time.time()
            # LLAMADA AL MOTOR REAL
            success = execute_task(
                nc_path=str(nc_in), 
                dict_output=dict_out_flat, 
                overwrite=overwrite
            )
            
            if success:
                # Marcamos como procesado en el inventario original
                inventory[fid]['status']['is_processed'] = True
                print(f"    ✅ OK ({round(time.time() - start_scene, 2)}s)")
            else:
                print(f"    ❌ Executor devolvió False")
                
        except Exception as e:
            print(f"    ❌ Error crítico: {e}")
            traceback.print_exc()

        # Guardado incremental para no perder el avance
        with open(path_p, 'w') as f:
            json.dump(plan, f, indent=4)

    print(f"\n🏁 {ctx} Misión completada en {round(time.time() - start_job, 2)}s")
    return True
