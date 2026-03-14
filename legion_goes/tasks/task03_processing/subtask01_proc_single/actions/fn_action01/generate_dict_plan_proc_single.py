# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/generate_dict_plan_proc_single.py
# Version: 1.0.3 (Fixed Inventory Mapping & v.0.0.1 Standard)
# =============================================================================

import json
from pathlib import Path

# --- LONG PATH IMPORTS (Absolute Project Paths) ---
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict01_self_info
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict02_sat_prod_info
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict03_inventory
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict04_summary

def generate_dict_plan_proc_single(
    sat_id: str, 
    product_id: str, 
    year: str, 
    day: str, 
    fnp_tag: str = "fnp01",
    save_json: bool = True
) -> dict:
    """
    Assembles the 4 dictionary parts. 
    Fixed: Directly captures inventory from Step 03 and uses 'inventory' key for symmetry.
    """
    
    # 1. Metadata & Absolute Path for the Plan
    dict01 = generate_dict01_self_info.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )
    
    # 2. Technical Satellite/Product Info (SOT)
    dict02 = generate_dict02_sat_prod_info.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day
    )
    
    # 3. Processing Inventory (Definition/Tracking)
    # FIX: Ahora la función devuelve directamente el diccionario del inventario
    inventory = generate_dict03_inventory.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )
    
    # 4. Progress Summary (Usando el inventario recién generado)
    dict04 = generate_dict04_summary.generate_dict(dict_proc_inventory=inventory)
    
    # --- FINAL ASSEMBLY (Standardized v.0.0.1) ---
    plan_dict = {
        "self_info": dict01,
        "sat_prod_info": dict02,
        "summary": dict04,
        "inventory": inventory  # Nombre de llave simplificado para ser simétrico con download
    }

    # --- SAVE TO DISK ---
    if save_json:
        abs_file_path = Path(dict01["path_absolute"])
        abs_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
            
        print(f"💾 [SAVED] Processing Plan: {abs_file_path}")
    
    return plan_dict

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " LEGION-GOES: GENERATE PROCESSING PLAN ".center(80, "="))
    
    # Usamos parámetros que sabemos que tienen descarga (G19, Día 003)
    T_PARAMS = {
        "sat_id": "19",
        "product_id": "ABI-L2-MCMIPF",
        "year": "2026",
        "day": "003",
        "fnp_tag": "fnp01"
    }

    try:
        full_plan = generate_dict_plan_proc_single(**T_PARAMS, save_json=True)
        
        # Validaciones de salida
        items_count = len(full_plan["inventory"])
        print(f"✅ Success: Plan generated for {T_PARAMS['product_id']}")
        print(f"📊 Items in Inventory: {items_count}")
        print(f"📈 Progress: {full_plan['summary']['status']['progress_percentage']}")
        
    except Exception as e:
        print(f"❌ [CRITICAL ERROR]: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80 + "\n")
