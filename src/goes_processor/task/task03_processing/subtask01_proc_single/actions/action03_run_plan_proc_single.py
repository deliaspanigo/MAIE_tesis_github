"""
Path: src/goes_processor/task/task03_processing/subtask01_proc_single/actions/action03_run_plan_proc_single.py
Version: 2.1.0
Description: Orquestador Maestro Multi-Producto. 
             Estructura preparada para MCMIPF, LSTF, FDCF, etc.
"""

import json
import gc
from pathlib import Path
from datetime import datetime

# --- IMPORTACIONES DE ACCIONES BASE ---
try:
    from actions.action01_gen_plan_proc_single import gen_and_save_plan_proc_single
    from actions.action02_check_plan_proc_single import run_integrity_check_by_params
    
    # --- IMPORTACIONES POR PRODUCTO (Alias: producto_fnpXX_...) ---
    
    # 1. PRODUCTO: MCMIPF (Cloud & Moisture Imagery)
    from actions.fnp.ABI_L2_MCMIPF_SP_single_fnp01.code_python_proc_single import (
        execute_fnp_processing as mcmipf_fnp01_func, 
        dict_output_schema as mcmipf_fnp01_dict, 
        verify_fnp_interface as mcmipf_fnp01_verify
    )
    from actions.fnp.ABI_L2_MCMIPF_SP_single_fnp02.code_python_proc_single import (
        execute_fnp_processing as mcmipf_fnp02_func, 
        dict_output_schema as mcmipf_fnp02_dict, 
        verify_fnp_interface as mcmipf_fnp02_verify
    )

    # 2. PRODUCTO: LSTF (Land Surface Temperature) - Ejemplo de cómo agregarías el siguiente
    # from actions.fnp.ABI_L2_LSTF_SP_single_fnp01.code_python_proc_single import (
    #     execute_fnp_processing as lstf_fnp01_func, 
    #     dict_output_schema as lstf_fnp01_dict, 
    #     verify_fnp_interface as lstf_fnp01_verify
    # )

except ImportError as e:
    print(f"❌ Error de importación en Action03: {e}")
    raise

# =============================================================================
# 1. CATÁLOGO MAESTRO DE PRODUCTOS (Extensible)
# =============================================================================
CATALOGO_PRODUCTOS = {
    "MCMIPF": {
        "full_name": "ABI-L2-MCMIPF",
        "fnps": {
            "fnp01": {
                "id": "fnp01", 
                "func": mcmipf_fnp01_func, 
                "schema": mcmipf_fnp01_dict,
                "verifier": mcmipf_fnp01_verify
            },
            "fnp02": {
                "id": "fnp02", 
                "func": mcmipf_fnp02_func, 
                "schema": mcmipf_fnp02_dict,
                "verifier": mcmipf_fnp02_verify
            }
        }
    },
    # Cuando tengas LSTF, solo descomentas y agregas aquí:
    # "LSTF": {
    #     "full_name": "ABI-L2-LSTF",
    #     "fnps": {
    #         "fnp01": { "id": "fnp01", "func": lstf_fnp01_func, "schema": lstf_fnp01_dict, "verifier": lstf_fnp01_verify }
    #     }
    # }
}

# =============================================================================
# 2. MOTOR DE EJECUCIÓN UNITARIA
# =============================================================================

def execute_proc_single_by_product(product_name: str, path_plan_proc: Path, overwrite: bool = False):
    """
    Ejecuta el procesamiento buscando la configuración en el catálogo dinámico.
    """
    with open(path_plan_proc, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    inventory = plan.get("proc_single_inventory", {})
    fnp_tag = plan["plan_proc_single_self_info"]["fnp_tag"]
    
    # Obtener configuración del catálogo
    product_cfg = CATALOGO_PRODUCTOS.get(product_name)
    if not product_cfg:
        print(f"❌ Producto {product_name} no configurado en el catálogo.")
        return
        
    fnp_config = product_cfg["fnps"].get(fnp_tag)
    if not fnp_config:
        print(f"❌ FNP {fnp_tag} no encontrada para {product_name}.")
        return

    # Verificación de Interfaz
    is_ok, msg = fnp_config["verifier"](fnp_config["schema"], fnp_config["func"])
    if not is_ok:
        print(f"🛑 [INTERFACE ERROR] {product_name}-{fnp_tag}: {msg}")
        return

    print(f"🚀 Procesando {len(inventory)} items ({product_name} - {fnp_tag})...")

    count_ok = 0
    for fid, item in inventory.items():
        if not item["status"].get("is_ready_to_proc"):
            continue

        if not overwrite and item["status"].get("is_done"):
            count_ok += 1
            continue

        nc_in = item["input_ref"]["path_absolute"]
        out_paths = item["output_ref"]["paths_absolute"]

        try:
            success = fnp_config["func"](nc_path=nc_in, overwrite=overwrite, **out_paths)
            if success:
                item["status"]["is_done"] = True
                item["status"]["last_processed"] = datetime.now().isoformat()
                item["status"]["error"] = None
                count_ok += 1
        except Exception as e:
            item["status"]["error"] = str(e)
            print(f"❌ Error en {fid}: {e}")
        
        gc.collect()

    with open(path_plan_proc, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=4)
    
    print(f"✅ [{product_name}-{fnp_tag}] Finalizado: {count_ok}/{len(inventory)}")


# =============================================================================
# 3. ORQUESTADOR MAESTRO
# =============================================================================

def orchestrate_full_product(product_name: str, year: int, day: int, sat_pos: str, output_folder_base: str, overwrite: bool = False):
    """
    Pipeline total agnóstico al producto.
    """
    print(f"\n{'='*60}")
    print(f"🌟 MAIE PIPELINE v.2.1 | PRODUCTO: {product_name} ({year}-{day})")
    print(f"{'='*60}")

    product_info = CATALOGO_PRODUCTOS.get(product_name)
    if not product_info:
        print(f"❌ Error: El producto '{product_name}' no existe en CATALOGO_PRODUCTOS.")
        return

    for fnp_id, fnp_entry in product_info["fnps"].items():

        # PASO 1: Plan
        print(f"\n📂 [1/3] Generando Plan: {product_name} - {fnp_id}")
        path_plan = gen_and_save_plan_proc_single(
            year=year, day=day, sat_pos=sat_pos,
            product_id=product_info["full_name"],
            output_folder_base=output_folder_base,
            dict_output_names=fnp_entry["schema"],
            fnp_tag=fnp_id
        )

        # PASO 2: Audit
        print(f"🔍 [2/3] Auditando Integridad física...")
        run_integrity_check_by_params(
            year=year, day=day, sat_pos=sat_pos, 
            product_id=product_info["full_name"], fnp_tag=fnp_id
        )

        # PASO 3: Run
        print(f"🚀 [3/3] Iniciando Procesamiento...")
        execute_proc_single_by_product(
            product_name=product_name,
            path_plan_proc=path_plan,
            overwrite=overwrite
        )

    print(f"\n✨ PROCESO COMPLETADO PARA: {product_name}")
    print(f"{'='*60}\n")
