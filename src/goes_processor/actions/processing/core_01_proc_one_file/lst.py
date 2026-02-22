# Version: v.0.5.0 (LST Orchestrator - Path Refactoring with Hourly Folders)
import sys
import json
import warnings
import numpy as np
import time
import os
import matplotlib
# Force non-interactive backend to prevent Tcl/Tkinter thread errors in CLI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

warnings.filterwarnings("ignore")

class SmartIndentedOutput:
    """
    Captures output and applies double indentation for library logs.
    """
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "
        self.newline = True

    def write(self, text):
        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                if not any(icon in line for icon in ["⏰", "📁", "📂", "🧠", "📦", "📸", "🗺️", "🔄", "💾", "✅", "🏁", "⏱️", "❌"]):
                    self.original_stream.write(self.base_indent + self.extra_indent + line)
                else:
                    self.original_stream.write(self.base_indent + line)
            else:
                self.original_stream.write(line)
            self.newline = line.endswith('\n')

    def flush(self):
        self.original_stream.flush()

# --- ORCHESTRATOR ---

def process_lst_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Sequential Orchestrator for LST Module.
    Structure: output / satellite / product / year / day / hour / time_lapse / filename
    """
    file_path = Path(input_file).resolve()
    base_name = file_path.stem
    
    # 1. CENTRALIZED PATH LOGIC (GOES-R Filename Parsing)
    parts = base_name.split('_')
    # noaa-goes19, noaa-goes18, etc.
    sat_name = f"noaa-goes{parts[2].replace('G', '')}"
    # ABI-L2-LSTF (rsplit used to avoid breaking names with internal 'M')
    product_raw = parts[1]
    product_clean = product_raw.rsplit('-M', 1)[0] if '-M' in product_raw else product_raw
    
    # Time parsing from part 3: sYYYYJJJHHMMSS (e.g., s20260031430...)
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10] # Extracting HH

    # Common root path with the new Hourly hierarchy
    # Path: output/noaa-goes19/ABI-L2-LSTF/2026/003/14/time_lapse_01hour/OR_ABI...
    product_out_root = output_base / sat_name / product_clean / year / day / hour / "time_lapse_01hour" / base_name
    
    success_report = {"stage_01": False}
    
    # Execute Stage 01
    success_report["stage_01"] = fn01_lst_generate_products(
        file_path, product_out_root, overwrite, indent
    )
    
    return success_report

# --- STAGE FUNCTIONS ---

def fn01_lst_generate_products(file_path: Path, product_out_root: Path, overwrite=False, indent=""):
    """
    Stage 01: Multi-Product Generation (Grayscale Celsius & Custom Color).
    """
    start_time = datetime.now()
    start_ts = time.time()
    base_name = file_path.stem
    
    # Redirect logs for CLI reporting
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # Define and create specific folder for this function
        fn_dir = product_out_root / "fn01"
        fn_dir.mkdir(parents=True, exist_ok=True)

        # 1. SATPY CACHE CONFIGURATION
        path_cache = satpy_config.get("cache_dir")
        if path_cache: 
            os.environ['PYRESAMPLE_CACHE_DIR'] = str(path_cache)

        print(f"⏰ [fn01] Start: {start_time.strftime('%H:%M:%S')}")

        # Overwrite protection
        output_check = fn_dir / f"{base_name}_wgs84_color.png"
        if not overwrite and output_check.exists():
            print(f"✅ [fn01] Skipping: Products already exist in {fn_dir.name}")
            return True

        # 2. DATA LOADING
        print(f"📦 [fn01] [1/6] Loading Raw LST and Color composites...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        prod_raw = 'LST'
        prod_color = 'lst_celsius_color01' 
        scn.load([prod_raw, prod_color])

        # 3. SCIENTIFIC CONVERSION (Kelvin to Celsius)
        if scn[prod_raw].mean() > 100:
            print(f"🧠 [fn01] Converting Kelvin to Celsius...")
            scn[prod_raw] = scn[prod_raw] - 273.15
            scn[prod_raw].attrs['units'] = 'Celsius'
            
            if prod_color in scn:
                scn[prod_color].data = scn[prod_raw].data
                scn[prod_color].attrs['units'] = 'Celsius'

        # 4. NATIVE EXPORT
        print(f"📸 [fn01] [2/6] Generating native plots...")
        scn.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_native_gray.png"), writer='simple_image')
        scn.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_native_color.png"), writer='simple_image')

        # 5. RESAMPLING
        print(f"🔄 [fn01] [3/6] Resampling to WGS84 (Global 3600x1800)...")
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 
                                  3600, 1800, [-180, -90, 180, 90])
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # 6. FINAL EXPORT
        print(f"💾 [fn01] [4/6] Saving GeoTIFFs...")
        scn_res.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_wgs84_celsius_data.tif"), writer='geotiff')
        scn_res.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_wgs84_color_visual.tif"), writer='geotiff')

        print(f"📸 [fn01] [5/6] Saving WGS84 PNGs...")
        scn_res.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_wgs84_gray.png"), writer='simple_image')
        scn_res.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_wgs84_color.png"), writer='simple_image')

        # 7. AUDIT METADATA
        print(f"📸 [fn01] [6/6] Saving Metadata JSON...")
        duration = round((time.time() - start_ts) / 60, 2)
        meta = {
            "source_file": file_path.name,
            "version": "v.0.5.0",
            "stage": "fn01",
            "duration_min": duration,
            "timestamp": datetime.now().isoformat()
        }
        with open(fn_dir / f"{base_name}_metadata_fn01.json", 'w') as f:
            json.dump(meta, f, indent=4)

        print(f"✅ [fn01] Pipeline complete ({duration} min).")
        return True

    except Exception as e:
        print(f"❌ [fn01] CRITICAL ERROR: {str(e)}")
        return False
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
