"""
Path: legion_goes/code/python_sp/f01_donwload/utils/generate_plan_download_json_file_path.py
Version: 1.1.0
Description: Generates the absolute path for the Task 02 download plan JSON file.
"""

from pathlib import Path
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder
from legion_goes.code.python_sp.f01_donwload.utils.generate_plan_download_json_file_name import generate_plan_download_json_file_name


def generate_plan_download_json_file_path(sat_id: str, product_id: str, year: str, day: str) -> Path:
    """
    Constructs the full system path where the download plan will be stored.
    Structure: [plans_root] / [product_id] / [year] / [filename]
    
    Returns:
        Path: Absolute pathlib.Path object.
    """
    # 1. Get the base root folder for download plans from SOT
    plans_root = get_SOT_specific_folder(key="data_plan")
    
    # 2. Generate the standardized filename using the specific function
    file_name = generate_plan_download_json_file_name(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day
    )
    
    # 3. Build the organized directory structure
    # We group by product and then by year to avoid having thousands of files in one folder
    full_path = Path(plans_root) / str(year) / str(day) /file_name
    
    return full_path

# =============================================================================
# QUICK TEST
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: DOWNLOAD PLAN PATH GENERATION ".center(60, "="))
    
    T_SAT = "16"
    T_PROD = "ABI-L2-MCMIPF"
    T_YEAR = "2026"
    T_DAY = "070"

    try:
        target_path = generate_plan_download_json_file_path(T_SAT, T_PROD, T_YEAR, T_DAY)
        
        print(f"✅ Target Path Generated:")
        print(f"   {target_path}")
        
        # Verify if parent directories exist (optional diagnostic)
        if not target_path.parent.exists():
            print(f"\n💡 Note: Parent directory does not exist yet.")
            print(f"   It will be created by the 'save' function.")

    except Exception as e:
        print(f"❌ Path generation failed: {e}")

    print("=" * 60 + "\n")
