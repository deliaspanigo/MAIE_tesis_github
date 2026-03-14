# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/action01_create_json_plan_proc_single.py
# Version: 1.9.2 (Fixed Parameter Sync & Double-Save Conflict)
# =============================================================================
import os
from pathlib import Path

# --- ABSOLUTE IMPORTS ---
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.generate_plan_proc_single_json_file_path import generate_plan_proc_single_json_file_path
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.generate_dict_plan_proc_single import generate_dict_plan_proc_single

def run_action(
    sat_id: str,
    product_id: str,
    year: str,
    day: str,
    fnp_tag: str, 
    overwrite_json_plan: bool = False
):
    """
    Orchestrates Action 01. 
    Logic: Check existence -> Handle Overwrite -> Generate & Save.
    """
    ctx = "[Action01 - Create Processing Plan JSON]"
    
    # 1. Resolve expected plan path using the official utility
    path_plan_expected = generate_plan_proc_single_json_file_path(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day,
        fnp_tag=fnp_tag
    )
    
    file_exists = path_plan_expected.exists()

    print(f"\n{'='*80}")
    print(f"🚀 {ctx}".center(80))
    print(f"{'='*80}")
    print(f"📂 INFO: [satellite: G{sat_id}] | [product: {product_id}] | [year: {year}] | [day: {day}] | [tag: {fnp_tag}]")
    print(f"📂 TARGET: {path_plan_expected}")
    print(f"📂 DETAILS: [exists: {file_exists}] | [overwrite: {overwrite_json_plan}]")
    print(f"{'-'*80}")

    # --- LOGIC MATRIX ---

    # Si ya existe y NO queremos sobrescribir, salimos felices
    if file_exists and not overwrite_json_plan:
        print(f"⚠️  STATUS: Plan already exists. [OVERWRITE=FALSE]. Skipping.")
        return True

    # Si existe y SI queremos sobrescribir, borramos el viejo para evitar colisiones
    if file_exists and overwrite_json_plan:
        print(f"🔥 STATUS: Overwrite enabled. Deleting old file...")
        try:
            path_plan_expected.unlink()
            print(f"🗑️  Deleted: {path_plan_expected.name}")
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False

    # 3. Generation Process
    try:
        print(f"⚙️  Generating processing plan for Day {day}...")
        
        # IMPORTANTE: generate_dict_plan_proc_single YA GUARDA el archivo internamente
        # usando la ruta absoluta definida en el Step 01 (Self Info).
        # Ponemos save_json=True para delegar el guardado al orquestador especializado.
        dict_plan_proc = generate_dict_plan_proc_single(
            sat_id=sat_id, 
            product_id=product_id, 
            year=year, 
            day=day,
            fnp_tag=fnp_tag,
            save_json=True 
        )
        
        # --- PHYSICAL DISK VERIFICATION ---
        if path_plan_expected.exists():
            print(f"✅ SUCCESS: Processing plan generated and verified on disk.")
            print("\n" + "=" * 80)
            print(f" RESULT: ✅ SUCCESS ".center(80))
            print("=" * 80 + "\n")
            return True
        else:
            print(f"❌ ERROR: Process finished but the file is missing from expected path.")
            return False
    
    except Exception as e:
        print(f"❌ FATAL ERROR during generation:\n💬 Detail: {e}\n")
        import traceback
        traceback.print_exc()
        return False

# ===================================================================
# MAIN EXECUTION
# ===================================================================
if __name__ == "__main__":
    params = {
        "sat_id": "19",
        "product_id": "ABI-L2-LSTF",
        "year": "2026",
        "day": "003",
        "fnp_tag": "fnp01",
        "overwrite_json_plan": True 
    }

    run_action(**params)
