# src/goes19_processor/processing/logic_how/truecolor.py

import sys
import json
import warnings
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
    """
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "  # 4 extra spaces for sub-messages
        self.newline = True

    def write(self, text):
        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                # Si la línea NO empieza con uno de tus íconos, le ponemos tabulación extra
                # Esto identifica mensajes externos como "No sensor name..."
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
    True Color Processor with Smart Sub-indentation for external library logs.
    v.0.0.1 - Monolithic Robust English Version
    """
    start_time = datetime.now()
    start_ts = time.time()
    
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Use the SmartIndentedOutput to handle the sub-indentation
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        if isinstance(input_file, list): input_file = input_file[0]
        file_path = Path(input_file).resolve()
        base_name = file_path.stem
        
        path_cache = satpy_config.get("cache_dir")
        os.environ['PYRESAMPLE_CACHE_DIR'] = path_cache

        rel_path = file_path.relative_to(input_base)
        out_dir = output_base / rel_path.parent / base_name
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"⏰ Start time: {start_time.strftime('%H:%M:%S')}")
        print(f"📁 Source: {file_path.name}")
        print(f"📂 Output: {out_dir}")
        print(f"🧠 Cache: {path_cache}")

        # --- STEP 1 ---
        print(f"📦 [1/5] Loading Scene (abi_l2_nc)...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['true_color'])

        # --- STEP 2 ---
        print(f"📸 [2/5] Generating native plot...")
        orig_img = out_dir / f"{base_name}_original_goes.png"
        scn.save_datasets(writer='simple_image', datasets=['true_color'], 
                          base_dir=str(out_dir), filename=orig_img.name)
        if orig_img.exists():
            print(f"   ✅ Confirmed: {orig_img.name}")

        # --- STEP 3 ---
        print(f"🗺️  [3/5] Defining WGS84 grid...")
        area_def = AreaDefinition(
            'global_wgs84', 'Lat-Lon Global', 'wgs84', 
            {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}, 
            3600, 1800, 
            (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )

        # --- STEP 4 ---
        print(f"🔄 [4/5] Resampling (kd_tree)...")
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # --- STEP 5 ---
        print(f"💾 [5/5] Exporting final products...")
        if format in ["png", "both"]:
            out_png = out_dir / f"{base_name}_wgs84.png"
            scn_res.save_datasets(writer='simple_image', datasets=['true_color'], 
                                  base_dir=str(out_dir), filename=out_png.name)
            if out_png.exists(): print(f"   ✅ Confirmed: {out_png.name}")

        if format in ["tif", "both"]:
            out_tif = out_dir / f"{base_name}_wgs84.tif"
            scn_res.save_datasets(writer='geotiff', datasets=['true_color'], 
                                  base_dir=str(out_dir), filename=out_tif.name, include_alpha=True)
            if out_tif.exists(): print(f"   ✅ Confirmed: {out_tif.name}")

        # --- FINAL REPORT ---
        end_time = datetime.now()
        duration_mins = (time.time() - start_ts) / 60
        
        print(f"🏁 End time: {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Duration: {duration_mins:.2f} minutes")
        print("-" * 50)
        
        return out_dir

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        raise e
        
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
