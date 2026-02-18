import sys
import json
import warnings
import time
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

warnings.filterwarnings("ignore")

class SmartIndentedOutput:
    """
    Output capturer with double indentation for external Satpy/Pyresample messages.
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

def fn01_mcmip_true_color_generate_products(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Core logic for True Color product generation (v0.3.3).
    """
    start_ts = time.time()
    report = {"mcmip_gen": False}
    
    # Path Resolution
    file_path = Path(input_file).resolve()
    input_base = Path(input_base).resolve()
    output_base = Path(output_base).resolve()
    
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        base_name = file_path.stem
        path_cache = satpy_config.get("cache_dir")
        
        rel_path = file_path.relative_to(input_base)
        out_dir = output_base / rel_path.parent / base_name / "fn01"
        out_dir.mkdir(parents=True, exist_ok=True)

        out_png_native = out_dir / f"{base_name}_original_goes.png"
        out_png_wgs84 = out_dir / f"{base_name}_wgs84.png"
        out_tif_wgs84 = out_dir / f"{base_name}_wgs84.tif"
        out_json = out_dir / f"{base_name}_metadata.json"

        if not overwrite and out_png_native.exists() and out_png_wgs84.exists() and out_tif_wgs84.exists() and out_json.exists():
            print(f"⚠️  [fn01] Skipping: All products already exist in fn01 folder.")
            report["mcmip_gen"] = True
            return report

        print(f"⏰ [fn01] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # STEP 1: Load
        print(f"📦 [fn01] [1/6] Loading Scene...")
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['true_color'])

        # STEP 2: Native PNG
        print(f"📸 [fn01] [2/6] Generating native plot...")
        if not out_png_native.exists() or overwrite:
            scn.save_datasets(writer='simple_image', datasets=['true_color'], 
                              base_dir=str(out_dir), filename=out_png_native.name)

        # STEP 3: Grid
        print(f"🗺️  [fn01] [3/6] Defining WGS84 grid...")
        area_def = AreaDefinition(
            'global_wgs84', 'Lat-Lon Global', 'wgs84', 
            {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}, 
            3600, 1800, 
            (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )

        # STEP 4: Resample
        print(f"🔄 [fn01] [4/6] Resampling (kd_tree)...")
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # STEP 5: Export WGS84
        print(f"💾 [fn01] [5/6] Exporting WGS84 products (PNG + TIF)...")
        if not out_png_wgs84.exists() or overwrite:
            scn_res.save_datasets(writer='simple_image', datasets=['true_color'], 
                                  base_dir=str(out_dir), filename=out_png_wgs84.name)
        
        if not out_tif_wgs84.exists() or overwrite:
            scn_res.save_datasets(writer='geotiff', datasets=['true_color'], 
                                  base_dir=str(out_dir), filename=out_tif_wgs84.name)

        # STEP 6: Metadata
        print(f"🧠 [fn01] [6/6] Saving metadata JSON...")
        metadata = {
            "source_file": str(file_path.name),
            "execution_time": datetime.now().isoformat(),
            "product_id": "MCMIP_TRUE_COLOR",
            "pipeline_version": "0.3.3",
            "status": "completed"
        }
        with open(out_json, 'w') as f:
            json.dump(metadata, f, indent=4)

        if out_png_native.exists() and out_tif_wgs84.exists():
            report["mcmip_gen"] = True

        duration = (time.time() - start_ts) / 60
        print(f"🏁 [fn01] Finished in {duration:.2f} min")
        
        return report

    except Exception as e:
        print(f"❌ [fn01] ERROR: {str(e)}")
        return report
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr

# ESTA ES LA FUNCIÓN QUE CAUSABA EL ERROR DE IMPORTACIÓN
def process_mcmip_true_color_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Exact name required by cli_core01.py
    """
    return fn01_mcmip_true_color_generate_products(
        input_file, input_base, output_base, overwrite, indent
    )
