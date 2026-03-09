"""
Path: src/legion_goes/task/task03_pro_single/actions/action03_run_plan_proc_single.py
Version: 2.2.7 (Dynamic Path + SoT Integration)
Description: Orquestador Maestro. Utiliza el generador oficial de nombres para localizar 
             el plan y delega la ejecución completa a los archivos fn02_executor.py.
"""

import sys
import json
import gc
import importlib.util
from pathlib import Path
from datetime import datetime

# --- IMPORTACIONES DE ACCIONES Y NOMBRES (SoT) ---
try:
    from action01_gen_plan_proc_single import gen_and_save_plan_proc_single
    from action02_check_plan_proc_single import run_integrity_check_by_params
    from fn01_file_name_plan_proc_single import get_plan_proc_single_file_path
except ImportError:
    # Soporte para ejecución cuando se importa desde fuera del paquete actions
    from actions.action01_gen_plan_proc_single import gen_and_save_plan_proc_single
    from actions.action02_check_plan_proc_single import run_integrity_check_by_params
    from actions.fn01_file_name_plan_proc_single import get_plan_proc_single_file_path

# =============================================================================
# 1. CARGADOR DINÁMICO DE MÓDULOS (Aisla entornos de FNP)
# =============================================================================

def load_fnp_module(fnp_folder_name, module_filename):
    """
    Carga fn01/fn02 inyectando su carpeta en sys.path para que los imports 
    internos (sin puntos) funcionen tanto en Notebooks como en Action03.
    """
    current_dir = Path(__file__).parent
    target_dir = current_dir / "fnp" / fnp_folder_name
    
    if not target_dir.exists():
        raise FileNotFoundError(f"No se encuentra la carpeta: {target_dir}")

    # Inyectar temporalmente el path de la subcarpeta del producto
    if str(target_dir) not in sys.path:
        sys.path.insert(0, str(target_dir))

    module_path = target_dir / module_filename
    spec = importlib.util.spec_from_file_location(f"{fnp_folder_name}.{module_filename}", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

# =============================================================================
# 2. CATÁLOGO DE CARPETAS FÍSICAS
# =============================================================================
CATALOGO_FNP_FOLDERS = {
    "MCMIPF": {
        "fnp01": "ABI_L2_MCMIPF_SP_single_fnp01",
        "fnp02": "ABI_L2_MCMIPF_SP_single_fnp02"
    },
    "LSTF": {
        "fnp01": "ABI_L2_LSTF_SP_single_fnp01",
        "fnp02": "ABI_L2_LSTF_SP_single_fnp02"
    }
}

# =============================================================================
# 3. MOTOR DE EJECUCIÓN (DELEGA A FN02)
# =============================================================================

def execute_proc_single_by_product(product_name: str, path_plan_proc: Path, overwrite: bool = False):
    """
    Lee el plan y para cada escena marcada como 'ready', dispara el run_executor.
    """
    if not path_plan_proc.exists():
        print(f"❌ Error: No se encuentra el archivo de plan en {path_plan_proc}")
        return

    with open(path_plan_proc, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    inventory = plan.get("proc_single_inventory", {})
    fnp_tag = plan["plan_proc_single_self_info"]["fnp_tag"]
    
    folder_name = CATALOGO_FNP_FOLDERS.get(product_name, {}).get(fnp_tag)
    if not folder_name:
        print(f"❌ Carpeta no mapeada para {product_name}-{fnp_tag}")
        return

    # Cargar fn02_executor dinámicamente
    try:
        fnp_executor = load_fnp_module(folder_name, "fn02_executor.py")
    except Exception as e:
        print(f"❌ Fallo al cargar ejecutor de {fnp_tag}: {e}")
        return

    total_items = len(inventory)
    print(f"🚀 [MOTOR] Procesando {fnp_tag} ({total_items} escenas)...")

    count_ok = 0
    for i, (fid, item) in enumerate(inventory.items(), 1):
        # SOLO PROCESA SI ACTION02 MARCÓ READY: TRUE
        if not item["status"].get("is_ready_to_proc"):
            continue

        nc_in = item["input_ref"]["path_absolute"]
        out_paths = item["output_ref"]["paths_absolute"]

        print(f"\n📦 [{i}/{total_items}] {Path(nc_in).name}")

        try:
            # Delegación total al fn02 del FNP
            success = fnp_executor.run_executor(
                nc_path=nc_in, 
                dict_output=out_paths, 
                overwrite=overwrite
            )
            
            if success:
                item["status"]["is_done"] = True
                item["status"]["last_processed"] = datetime.now().isoformat()
                count_ok += 1
            else:
                print(f"⚠️ El ejecutor reportó fallo en esta escena.")

        except Exception as e:
            print(f"❌ Error crítico en motor: {e}")
            item["status"]["error"] = str(e)
        
        gc.collect()

    # Guardar progreso en el plan
    with open(path_plan_proc, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=4)
    
    print(f"\n🏁 [{fnp_tag}] Finalizado. Exitosos: {count_ok}/{total_items}")

# =============================================================================
# 4. ORQUESTADOR MAESTRO
# =============================================================================

def orchestrate_full_product(product_name: str, year: int, day: int, sat_pos: str, 
                            output_folder_base: str, overwrite: bool = False, 
                            fnp_tag: str = None):
    
    print(f"\n{'='*80}\n🌟 MAIE PIPELINE v.2.2.7 | {product_name} | SAT: {sat_pos}\n{'='*80}")

    tags_to_run = [fnp_tag] if fnp_tag else CATALOGO_FNP_FOLDERS.get(product_name, {}).keys()

    for t in tags_to_run:
        folder_name = CATALOGO_FNP_FOLDERS[product_name][t]
        
        # 1. Obtener schema de nombres (fn01)
        fnp_code = load_fnp_module(folder_name, "fn01_python_code.py")
        
        print(f"\n📂 [1/2] Generando/Cargando Plan para {t}...")
        
        # Llamamos a Action01 para asegurar que el plan existe y está actualizado
        path_plan = gen_and_save_plan_proc_single(
            year=year, day=day, sat_pos=sat_pos,
            product_id=f"ABI-L2-{product_name}",
            output_folder_base=output_folder_base,
            dict_output_names=fnp_code.dict_output_schema,
            fnp_tag=t,
            overwrite=overwrite
        )

        # 2. Ejecutar tareas delegando a fn02
        print(f"🚀 [2/2] Iniciando Tareas...")
        execute_proc_single_by_product(product_name, path_plan, overwrite)

    print(f"\n✨ PIPELINE FINALIZADO\n{'='*80}\n")
