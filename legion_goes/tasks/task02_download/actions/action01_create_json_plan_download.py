# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/action01_create_json_plan_download.py
# Version: 1.9.1 (Logic fix - Keeping user paths)
# =============================================================================
import os
from pathlib import Path

# --- ABSOLUTE IMPORTS (KEEPING YOUR PATHS) ---
from legion_goes.code.python_sp.f99_common.save_dict_plan_as_json_file import save_dict_plan_as_json_file
from legion_goes.code.python_sp.f01_donwload.utils.generate_plan_download_json_file_path import generate_plan_download_json_file_path
from legion_goes.tasks.task02_download.actions.fn_act01.generate_dict_plan_download import generate_dict_plan_download

def run_action(
    sat_id: str,
    product_id: str,
    year: str,
    day: str,
    overwrite_json_plan: bool = False
):
    """
    Orchestrates Action 01 using an explicit 2x2 logic matrix.
    """
    ctx = "[Action01 - Create Plan Download json]"
    
    # 1. Resolve expected plan path
    path_plan_expected = generate_plan_download_json_file_path(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day
    )
    
    # Ensure path_plan_expected is a Path object for .exists()
    if isinstance(path_plan_expected, str):
        path_plan_expected = Path(path_plan_expected)

    file_exists = path_plan_expected.exists()

    print(f"\n{'='*80}")
    print(f"🚀 {ctx}".center(80))
    print(f"{'='*80}")
    print(f"📂 INFO: [satellite: G{sat_id}] | [product: {product_id}] | [year: {year}] | [day: {day}]")
    print(f"📂 TARGET PATH: {path_plan_expected}")
    print(f"📂 DETAILS: [file_exists: {file_exists}] | [overwrite: {overwrite_json_plan}]")
    print(f"{'-'*80}")

    # --- LOGIC MATRIX ---
    if not file_exists:
        print(f"✨ STATUS: Plan does not exist. Proceeding with generation...")

    elif file_exists and not overwrite_json_plan:
        print(f"⚠️  STATUS: Plan already exists. [OVERWRITE=FALSE]. Skipping creation.")
        return True

    elif file_exists and overwrite_json_plan:
        print(f"🔥 STATUS: Plan exists and [OVERWRITE=TRUE]. Deleting old file...")
        try:
            path_plan_expected.unlink()
            print(f"🗑️  Deleted: {path_plan_expected.name}")
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False

    # 3. Generation Process
    try:
        print(f"⚙️  Generating a download plan for GOES-{sat_id} (Day {day})...")
        
        dict_plan_download = generate_dict_plan_download(
            sat_id=sat_id, 
            product_id=product_id, 
            year=year, 
            day=day
        )
        
        # 4. Save to Disk
        save_dict_plan_as_json_file(
            dict_plan=dict_plan_download, 
            path_json=str(path_plan_expected)
        )
        
        # --- PHYSICAL DISK VERIFICATION ---
        if path_plan_expected.exists():
            print(f"✅ SUCCESS: Download plan generated and verified on disk.")
            print("\n" + "=" * 80)
            # FIX: Removed the reference to 'success' variable that didn't exist here
            print(f" RESULT: ✅ SUCCESS ".center(80))
            print("=" * 80 + "\n")
            return True
        else:
            print(f"\n{'!'*80}")
            print(f" 🔥 CATASTROPHIC ERROR: Write operation confirmed but file missing! ".center(80))
            print(f"{'!'*80}\n")
            return False
    
    except Exception as e:
        print(f"❌ FATAL ERROR during generation:\n💬 Detail: {e}\n")
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
        "overwrite_json_plan": True 
    }

    success_result = run_action(**params)
