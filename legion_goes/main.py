# =============================================================================
# PATH: legion_goes/main.py
# Version: 1.8.6
# Description: Main entry point for GOES processing with global config and identity mapping.
# =============================================================================

# 1. NO NECESITAMOS importar my_config_satpy aquí
#    Ya se carga automáticamente al hacer import legion_goes (desde __init__.py)

# 2. STANDARD IMPORTS
from pathlib import Path

# 3. FNP MODULES
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fnps.ABI_L2_MCMIPF.fnp01 import fn01_python_code

def run_main():
    # --- INPUT DEFINITION ---
    # In a real scenario, this would come from a Loop or a Planner
    nc_file = Path("/ruta/a/tu/bulk/OR_ABI-L2-MCMIPF-M6_G19_s20260601200_test.nc")
   
    if not nc_file.exists():
        print(f"❌ Input file not found: {nc_file}")
        return
   
    # --- IDENTITY & PATH MAPPING ---
    # Extract the "DNI" (prefix) of the satellite file
    file_id = nc_file.stem
    output_dir = Path("./output_test") / file_id
    output_dir.mkdir(parents=True, exist_ok=True)
   
    # Build the dictionary for fnp01 using its internal schema
    processing_paths = {}
    for key, suffix in fn01_python_code.dict_output_schema.items():
        processing_paths[key] = str(output_dir / f"{file_id}_{suffix}")
   
    # --- EXECUTION ---
    print(f"🚀 Starting FNP01 for: {file_id}")
   
    success = fn01_python_code.fnp_python_code(
        nc_path=str(nc_file),
        **processing_paths
    )
   
    if success:
        print(f"✅ Processing finished. Check results in: {output_dir}")
    else:
        print(f"❌ FNP01 execution failed.")

if __name__ == "__main__":
    run_main()
