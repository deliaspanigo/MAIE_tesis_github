"""
Path: legion_goes/code/python_sp/f02_processing/sp001_single/f01_product_proc/ABI_L2_MCMIPF/fnp02/fn01_python_code.py
Version: 1.8.7
Description: FNP02 - Colorized Infrared (IR) Processing with transparency and **kwargs.
"""

import os
import sys
import time
import gc
import json
import warnings
import logging
import matplotlib
matplotlib.use('Agg') # Backend for servers
import numpy as np
from PIL import Image
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from satpy import Scene
from pyresample.geometry import AreaDefinition

# --- SILENCE SYSTEM STDERR ---
@contextmanager
def silence_stderr():
    """Redirects stderr to devnull to clean console from low-level library warnings."""
    new_target = open(os.devnull, "w")
    old_target = sys.stderr
    sys.stderr = new_target
    try:
        yield new_target
    finally:
        sys.stderr = old_target
        new_target.close()

# --- Silence Python Logs ---
warnings.filterwarnings("ignore")
logging.getLogger("satpy").setLevel(logging.ERROR)
logging.getLogger("pyresample").setLevel(logging.ERROR)

# =============================================================================
# 1. OUTPUT DEFINITION DICTIONARY
# =============================================================================
dict_output_schema = {
    "png_CRSnative_ir": "CRS-GoesEast_IR_Colorized.png",
    "png_CRSnative_ir_transparent": "CRS-GoesEast_IR_Colorized_Transparent.png",
    "png_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.png",
    "png_CRSwgs84_ir_transparent": "CRS-WGS84_IR_Colorized_Transparent.png",
    "tif_CRSwgs84_ir": "CRS-WGS84_IR_Colorized.tif",
    "json_meta": "meta.json",
    "gallery": "gallery.png"
}

# =============================================================================
# 2. INTERNAL UTILITIES
# =============================================================================

def apply_grayscale_transparency(input_path, output_path, saturation_threshold=20):
    """Converts grayscale pixels (clouds/background) to transparent for overlays."""
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    rgb = data[:, :, :3].astype(np.int16)
    
    # Calculate saturation to identify gray levels
    diff = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    gray_pixels = diff <= saturation_threshold
    
    # Set alpha channel to 0 for gray pixels
    data[gray_pixels, 3] = 0
    Image.fromarray(data).save(output_path)

# =============================================================================
# 3. PROCESSING FUNCTION
# =============================================================================

def fnp_python_code(nc_path, **kwargs):
    """
    Executes the FNP02 pipeline for Colorized IR.
    Uses **kwargs to receive file paths dynamically from the executor.
    """
    start_time = time.time()
    try:
        # Ensure output directory exists using the first available path
        primary_path = kwargs.get("png_CRSnative_ir")
        if primary_path:
            Path(primary_path).parent.mkdir(parents=True, exist_ok=True)

        # Step 01: Load Data
        print(f"      [Step 01/10] 🛰️  Loading IR Product...", end=" ", flush=True)
        with silence_stderr():
            scn = Scene(filenames=[str(nc_path)], reader='abi_l2_nc')
            product_id = 'colorized_ir_clouds'
            scn.load([product_id])
        print("Done.")

        # Step 02/03: Native IR & Transparency
        print(f"      [Step 02/10] 🖼️  Saving Native IR...", end=" ", flush=True)
        native_ir_path = kwargs.get("png_CRSnative_ir")
        scn.save_datasets(writer='simple_image', datasets=[product_id], filename=str(native_ir_path))
        print("Done.")
        
        print(f"      [Step 03/10] 🎭  Applying Transparency (Native)...", end=" ", flush=True)
        apply_grayscale_transparency(native_ir_path, kwargs.get("png_CRSnative_ir_transparent"))
        print("Done.")

        # Step 05/06: Resample to WGS84
        print(f"      [Step 05/10] 🗺️  Defining WGS84 Area...", end=" ", flush=True)
        area_def = AreaDefinition(
            'wgs84', 'LatLon', 'wgs84',
            {'proj': 'eqc', 'units': 'm', 'ellps': 'WGS84'},
            3600, 1800, (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )
        print("Done.")
        
        print(f"      [Step 06/10] 🔄  Resampling Scene to WGS84...", end=" ", flush=True)
        scn_res = scn.resample(area_def)
        print("Done.")

        # Step 07/08: Save WGS84 & Transparency
        print(f"      [Step 07/10] 💾  Saving WGS84 PNG and GeoTIFF...", end=" ", flush=True)
        wgs84_png_path = kwargs.get("png_CRSwgs84_ir")
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], filename=str(wgs84_png_path))
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], filename=str(kwargs.get("tif_CRSwgs84_ir")))
        print("Done.")

        print(f"      [Step 08/10] 🎭  Applying Transparency (WGS84)...", end=" ", flush=True)
        apply_grayscale_transparency(wgs84_png_path, kwargs.get("png_CRSwgs84_ir_transparent"))
        print("Done.")

        # Step 09: Metadata Generation
        print(f"      [Step 09/10] 📝  Generating Metadata...", end=" ", flush=True)
        duration = round(time.time() - start_time, 2)
        meta_path = kwargs.get("json_meta")
        if meta_path:
            with open(meta_path, 'w') as f:
                json.dump({
                    "source_file": Path(nc_path).name,
                    "execution_time_sec": duration,
                    "product_type": "COLORIZED_IR_CLOUDS",
                    "generation_timestamp": datetime.now().isoformat()
                }, f, indent=4)
        print("Done.")

        # Step 10: Memory Cleanup
        print(f"      [Step 10/10] 🧹  Cleaning memory buffers...", end=" ", flush=True)
        del scn; del scn_res; gc.collect()
        print(f"Done. (Total time: {duration}s)")
        
        return True

    except Exception as e:
        print(f"\n      ❌ [FNP02 ERROR] {str(e)}")
        return False

# =============================================================================
# DIAGNOSTIC MAIN (Terminal + Notebook Compatible)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " FNP02: DIAGNOSTIC EXECUTION (DYNAMIC) ".center(80, "="))
    
    # 1. Locate the first available .nc file in current directory
    try:
        current_dir = Path(__file__).parent.resolve()
    except NameError:
        current_dir = Path(os.getcwd()).resolve()

    nc_files = list(current_dir.glob("*.nc"))
    
    if not nc_files:
        print(f"❌ Error: No .nc files found in {current_dir}")
        sys.exit(1)
    
    selected_nc = nc_files[0]
    print(f"🎯 Detected File: {selected_nc.name}")

    # 2. Setup Test Output Directory
    test_folder = current_dir / "output_test_fnp02" / selected_nc.stem
    test_folder.mkdir(parents=True, exist_ok=True)
    
    # 3. Build Argument Dictionary (Mapping Schema to Real Paths)
    execution_args = {}
    for key, filename in dict_output_schema.items():
        if key != "gallery":
            execution_args[key] = str(test_folder / filename)

    # 4. Execute Processing with Splat Operator (**)
    print(f"📂 Output Folder: {test_folder}")
    print("-" * 80)
    
    success = fnp_python_code(nc_path=selected_nc, **execution_args)

    if success:
        print("\n" + "✅ PROCESSING COMPLETED SUCCESSFULLY ".center(80, "="))
    else:
        print("\n" + "❌ PROCESSING FAILED ".center(80, "="))
