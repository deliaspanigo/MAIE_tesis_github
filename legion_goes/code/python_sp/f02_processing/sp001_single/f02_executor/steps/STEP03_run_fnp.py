"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/steps/STEP03_run_fnp.py
Version: 0.0.1
Description: Runs the core processing function and handles gallery generation.
"""

from pathlib import Path

# --- UTILITY IMPORTS ---
from legion_goes.code.python_sp.sp001_single.f02_executor.utils.generate_fnp_preview_strip_gallery import generate_fnp_preview_strip_gallery

def STEP03_run_fnp(fnp_func, input_nc, dict_outputs, overwrite):
    """
    Core logic: runs FNP code and then the gallery utility.
    """
    # Filtramos 'gallery' para el core de procesamiento
    fn_kwargs = {k: v for k, v in dict_outputs.items() if k != 'gallery'}
    
    try:
        # Ejecución del núcleo (fnp_python_code)
        success = fnp_func(str(input_nc), **fn_kwargs)
        
        # Post-proceso: Galería
        if success and "gallery" in dict_outputs:
            gal_path = Path(dict_outputs["gallery"])
            generate_fnp_preview_strip_gallery(
                output_folder=str(gal_path.parent), 
                strip_filename=gal_path.name,
                overwrite=overwrite
            )
        return success
    except Exception as e:
        print(f"      ❌ [STEP03 ERROR]: {e}")
        return False
