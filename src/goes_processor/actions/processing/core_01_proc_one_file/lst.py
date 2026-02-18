import sys
import json
import warnings
import numpy as np
import time
import os
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

# --- STAGE FUNCTIONS ---

def fn01_lst_generate_products(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Stage 01: Multi-Product Generation (Grayscale Celsius & Custom Color).
    Inherits Satpy Config and Cache from main.py
    """
    start_time = datetime.now()
    start_ts = time.time()
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        if isinstance(input_file, list): input_file = input_file[0]
        file_path = Path(input_file).resolve()
        base_name = file_path.stem
        
        # 1. PATH RECOVERY FROM MAIN CONFIG
        path_cache = satpy_config.get("cache_dir")
        if path_cache: 
            os.environ['PYRESAMPLE_CACHE_DIR'] = str(path_cache)

        # 2. HIERARCHY SETUP (Based on GOES-R Filename Convention)
        parts = base_name.split('_')
        sat_name = f"noaa-goes{parts[2].replace('G', '')}"
        product_clean = parts[1].split('-M')[0]
        year, day = parts[3][1:5], parts[3][5:8]

        # Final Path: output / satellite / product / year / day / file_stem / fn01 /
        fn_dir = output_base / sat_name / product_clean / year / day / base_name / "fn01"
        fn_dir.mkdir(parents=True, exist_ok=True)

        print(f"⏰ [fn01] Start: {start_time.strftime('%H:%M:%S')}")

        # Overwrite protection
        if not overwrite and (fn_dir / f"{base_name}_wgs84_color.png").exists():
            print(f"✅  [fn01] Skipping: Products already exist.")
            return True

        # 3. LOAD DATA
        print(f"📦 [fn01] [1/6] Loading Raw LST and Color products...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        prod_raw = 'LST'
        prod_color = 'lst_celsius_color01' 
        scn.load([prod_raw, prod_color])

        # 4. SCIENTIFIC CONVERSION (Fixed to sync color data)
        if scn[prod_raw].mean() > 100:
            print(f"🧠 [fn01] Converting Kelvin to Celsius...")
            scn[prod_raw] = scn[prod_raw] - 273.15
            scn[prod_raw].attrs['units'] = 'Celsius'
            
            # Sincronizamos el producto de color con los datos restados
            if prod_color in scn:
                scn[prod_color].data = scn[prod_raw].data
                scn[prod_color].attrs['units'] = 'Celsius'

        # 5. EXPORT NATIVE (Geometry original)
        print(f"📸 [fn01] [2/6] Generating native plots...")
        scn.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_native_gray.png"), writer='simple_image')
        scn.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_native_color.png"), writer='simple_image')

        # 6. RESAMPLING (Using NN LUTs from satpy_cache)
        print(f"🔄 [fn01] [3/6] Resampling to WGS84 (Global 4326)...")
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # 7. FINAL EXPORTS (WGS84)
        print(f"💾 [fn01] [4/6] Saving GeoTIFFs (Data & Visual)...")
        scn_res.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_wgs84_celsius_data.tif"), writer='geotiff')
        scn_res.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_wgs84_color_visual.tif"), writer='geotiff')

        print(f"📸 [fn01] [5/6] Saving WGS84 PNGs...")
        scn_res.save_dataset(prod_raw, filename=str(fn_dir / f"{base_name}_wgs84_gray.png"), writer='simple_image')
        scn_res.save_dataset(prod_color, filename=str(fn_dir / f"{base_name}_wgs84_color.png"), writer='simple_image')

        # 8. METADATA FOR AUDIT
        print(f"📸 [fn01] [6/6] Saving JSON...")
        duration = round((time.time() - start_ts) / 60, 2)
        meta = {
            "source_file": file_path.name,
            "stage": "fn01",
            "products": ["raw_celsius", "enhanced_color"],
            "config_source": "main_py_global_config",
            "duration_min": duration
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

# --- MASTER PIPELINE ---

def process_lst_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Sequential Orchestrator for LST Module.
    """
    success_report = {"stage_01": False}
    
    # Run fn01
    success_report["stage_01"] = fn01_lst_generate_products(
        input_file, input_base, output_base, overwrite, indent
    )
    
    return success_report
