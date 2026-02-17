# src/goes_processor/processing/logic_how/lst.py

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
    Universal output capturer with double indentation for external messages.
    Ensures any library warning or error is further indented to the right.
    """
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "  # 4 extra spaces for sub-messages
        self.newline = True

    def write(self, text):
        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                # Check for our specific logging icons to apply base or extra indentation
                if not any(icon in line for icon in ["⏰", "📁", "📂", "🧠", "📦", "📸", "🗺️", "🔄", "💾", "✅", "🏁", "⏱️", "❌"]):
                    self.original_stream.write(self.base_indent + self.extra_indent + line)
                else:
                    self.original_stream.write(self.base_indent + line)
            else:
                self.original_stream.write(line)
            self.newline = line.endswith('\n')

    def flush(self):
        self.original_stream.flush()

def process_file(input_file, input_base: Path, output_base: Path, format="both", overwrite=False, indent=""):
    """
    LST Processor with Smart Sub-indentation and Thesis Timing.
    v.0.0.1 - Robust Monolithic English Version
    """
    # 0. TIMER AND REDIRECTION SETUP
    start_time = datetime.now()
    start_ts = time.time()
    
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Redirect both streams to capture any external library output
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # 1. PATH NORMALIZATION AND SETUP
        if isinstance(input_file, list): 
            input_file = input_file[0]
            
        file_path = Path(input_file).resolve()
        base_name = file_path.stem
        
        path_cache = satpy_config.get("cache_dir")
        os.environ['PYRESAMPLE_CACHE_DIR'] = path_cache

        rel_path = file_path.relative_to(input_base)
        out_dir = output_base / rel_path.parent / base_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # INITIAL LOGGING
        print(f"⏰ Start time: {start_time.strftime('%H:%M:%S')}")
        print(f"📁 Source: {file_path.name}")
        print(f"📂 Output: {out_dir}")

        # 2. LOAD LST DATA
        print(f"📦 [1/5] Loading LST products...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        prod_gray, prod_color = 'LST', 'lst_celsius_color01'
        scn.load([prod_gray, prod_color])

        # 3. UNIT CONVERSION (Fix Celsius)
        # Only apply if the mean temperature suggests Kelvin values (> 100)
        for p in [prod_gray, prod_color]:
            if scn[p].mean() > 100:
                scn[p] = scn[p] - 273.15
                scn[p].attrs['units'] = 'Celsius'

        # 4. SAVE NATIVE PLOTS
        print(f"📸 [2/5] Generating native plots...")
        native_png = out_dir / f"{base_name}_native_gray.png"
        scn.save_dataset(prod_gray, filename=str(native_png), writer='simple_image')
        if native_png.exists():
            print(f"   ✅ Confirmed: {native_png.name}")

        # 5. RESAMPLING
        print(f"🔄 [4/5] Resampling to WGS84 (kd_tree)...")
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # 6. EXPORT GeoTIFFs
        print(f"💾 [5/5] Exporting GeoTIFF products...")
        tif_path = out_dir / f"{base_name}_wgs84_data.tif"
        scn_res.save_dataset(prod_gray, filename=str(tif_path), writer='geotiff')
        if tif_path.exists():
            print(f"   ✅ Confirmed: {tif_path.name}")

        # 7. FINAL TIME REPORTING
        end_time = datetime.now()
        duration_mins = (time.time() - start_ts) / 60
        
        print(f"🏁 End time: {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Duration: {duration_mins:.2f} minutes")
        print("-" * 50)
        
        # Save JSON metadata for scientific record
        meta = {
            "source_file": file_path.name,
            "product": "LST",
            "processing_stats": {
                "start": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end": end_time.strftime('%Y-%m-%d %H:%M:%S'),
                "duration_min": round(duration_mins, 2)
            }
        }
        with open(out_dir / f"{base_name}_metadata.json", 'w') as f:
            json.dump(meta, f, indent=4)

        return out_dir

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        raise e
        
    finally:
        # RESTORE CONSOLE STREAMS
        sys.stdout = original_stdout
        sys.stderr = original_stderr
