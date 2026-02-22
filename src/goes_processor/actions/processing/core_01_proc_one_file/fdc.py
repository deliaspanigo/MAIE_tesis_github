# Version: v.0.5.1 (FDC Orchestrator - Fixed Return Report Type & Hourly Path)
import sys
import yaml
import warnings
import numpy as np
import time
import os
import matplotlib
# Force non-interactive backend to prevent Tcl/Tkinter thread errors in CLI
matplotlib.use('Agg')
from pathlib import Path
from datetime import datetime
from scipy.ndimage import label
from shapely.geometry import Point
import geopandas as gpd
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition
from satpy.enhancements.enhancer import get_enhanced_image

warnings.filterwarnings("ignore")

class SmartIndentedOutput:
    """Universal output capturer with indentation for clean reporting."""
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "
        self.newline = True

    def write(self, text):
        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                if not any(icon in line for icon in ["⏰", "📁", "📂", "🧠", "📦", "📸", "🗺️", "🔄", "💾", "✅", "🏁", "⏱️", "❌", "🛰️"]):
                    self.original_stream.write(self.base_indent + self.extra_indent + line)
                else:
                    self.original_stream.write(self.base_indent + line)
            else:
                self.original_stream.write(line)
            self.newline = line.endswith('\n')

    def flush(self):
        self.original_stream.flush()

# --- ORCHESTRATOR ---

def process_fdc_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Main Orchestrator for FDC Module.
    Structure: output / satellite / product / year / day / hour / time_lapse / filename
    """
    start_ts = time.time()
    file_path = Path(input_file).resolve()
    base_name = file_path.stem
    
    # 1. CENTRALIZED PATH LOGIC (GOES-R Parsing)
    parts = base_name.split('_')
    sat_name = f"noaa-goes{parts[2].replace('G', '')}"
    
    # Product naming (e.g., ABI-L2-FDCF)
    product_raw = parts[1]
    product_clean = product_raw.rsplit('-M', 1)[0] if '-M' in product_raw else product_raw

    # Time parsing from part 3: sYYYYJJJHHMMSS
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10]

    # Pre-calculated root directory including HOUR
    product_out_root = output_base / sat_name / product_clean / year / day / hour / "time_lapse_10minutes" / base_name
    
    # INITIALIZE REPORT FOR CLI COMPATIBILITY
    success_report = {"stage_01": False, "stage_02": False, "stage_03": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        print(f"⏰ [fdc] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Configure Satpy Cache
        path_cache = satpy_config.get("cache_dir")
        if path_cache: 
            os.environ['PYRESAMPLE_CACHE_DIR'] = str(path_cache)

        # Loading Scene
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['my_fdc_fn01', 'my_fdc_fn02', 'my_fdc_fn03'])

        # EXECUTE STAGES
        # Stage 01: Visuals (Returns scn_res for next stages)
        scn_res = fn01_process_visuals(scn, product_out_root, base_name, overwrite)
        success_report["stage_01"] = True
        
        # Stage 02: Analysis
        fn02_process_analysis(scn, scn_res, product_out_root, base_name, overwrite)
        success_report["stage_02"] = True
        
        # Stage 03: Vectorial
        fn03_process_vectorial(scn, scn_res, product_out_root, base_name, overwrite)
        success_report["stage_03"] = True
        
        duration = round((time.time() - start_ts) / 60, 2)
        print(f"✅ [fdc] Finished successfully in {duration} min.")
        return success_report

    except Exception as e:
        print(f"❌ [fdc] CRITICAL ERROR: {str(e)}")
        return success_report # Return current state to avoid CLI 'values' error
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr

# --- STAGE FUNCTIONS ---

def fn01_process_visuals(scn, product_out_root: Path, base_name, overwrite=False):
    """FN01: Standard visual masks (Solid PNG & GeoTIFF)."""
    fn_dir = product_out_root / "fn01"
    out_png = fn_dir / f"{base_name}_wgs84.png"
    
    area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])

    if not overwrite and out_png.exists():
        print(f"✅ [fn01] Products exist. Skipping and performing fast resampling.")
        return scn.resample(area_def, resampler='kd_tree')

    fn_dir.mkdir(parents=True, exist_ok=True)
    print(f"🧠 [fn01] Applying visual mask transparency logic...")
    data = scn['my_fdc_fn01']
    data_filled = data.where(~np.isnan(data), 40).where(data != 127, 40)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn01'] = data_filled

    print(f"📸 [fn01] Saving native projection plot...")
    get_enhanced_image(scn['my_fdc_fn01']).convert("RGB").save(str(fn_dir / f"{base_name}_native.png"))

    print(f"🔄 [fn01] Resampling to WGS84 (EPSG:4326)...")
    scn_res = scn.resample(area_def, resampler='kd_tree')

    print(f"💾 [fn01] Exporting WGS84 PNG & GeoTIFF...")
    get_enhanced_image(scn_res['my_fdc_fn01']).convert("RGB").save(str(out_png))
    scn_res.save_dataset('my_fdc_fn01', filename=str(fn_dir / f"{base_name}_wgs84.tif"), writer='geotiff')
    
    return scn_res

def fn02_process_analysis(scn, scn_res, product_out_root: Path, base_name, overwrite=False):
    """FN02: Data analysis plots (Dark Ramp)."""
    fn_dir = product_out_root / "fn02"
    out_png = fn_dir / f"{base_name}_wgs84.png"

    if not overwrite and out_png.exists():
        print(f"✅ [fn02] Analysis products exist. Skipping.")
        return

    fn_dir.mkdir(parents=True, exist_ok=True)
    print(f"🧠 [fn02] Applying analysis transparency logic...")
    data = scn['my_fdc_fn02']
    data_filled = data.where(~np.isnan(data), 127).where(data != 127, 127)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn02'] = data_filled

    print(f"📸 [fn02] Saving native plot (Analysis Ramp)...")
    get_enhanced_image(scn['my_fdc_fn02']).convert("RGB").save(str(fn_dir / f"{base_name}_native.png"))

    print(f"💾 [fn02] Saving WGS84 analysis products...")
    get_enhanced_image(scn_res['my_fdc_fn02']).convert("RGB").save(str(out_png))
    scn_res.save_dataset('my_fdc_fn02', filename=str(fn_dir / f"{base_name}_wgs84.tif"), writer='geotiff')

def fn03_process_vectorial(scn, scn_res, product_out_root: Path, base_name, overwrite=False):
    """FN03: Clustering and Vector export (GeoJSON, SHP)."""
    fn_dir = product_out_root / "fn03"
    vector_dir = fn_dir / "vectorial"
    out_geojson = vector_dir / f"{base_name}.geojson"

    if not overwrite and out_geojson.exists():
        print(f"✅ [fn03] Vectorial products exist. Skipping.")
        return

    shp_dir = vector_dir / "shapefile"
    for d in [fn_dir, vector_dir, shp_dir]: d.mkdir(parents=True, exist_ok=True)
    
    print(f"🧠 [fn03] Starting Full Analytics & Vector Export...")
    get_enhanced_image(scn['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_native.png"))
    get_enhanced_image(scn_res['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_wgs84.png"))

    fire_ids = [10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35]
    data_vals = scn_res['my_fdc_fn03'].values
    fire_mask = np.isin(data_vals, fire_ids)
    
    if not np.any(fire_mask):
        print(f"🏁 [fn03] No fire pixels detected. Skipping vector export.")
        return

    labeled_array, _ = label(fire_mask, structure=np.ones((3, 3)))
    lons, lats = scn_res['my_fdc_fn03'].attrs['area'].get_lonlats()
    
    records = []
    y_idx, x_idx = np.where(fire_mask)
    for r, c in zip(y_idx, x_idx):
        lat, lon = round(float(lats[r, c]), 6), round(float(lons[r, c]), 6)
        records.append({
            "source": f"{base_name}.nc",
            "fdcf_id": int(data_vals[r, c]),
            "lat": lat, "lon": lon,
            "cluster_id": int(labeled_array[r, c]),
            "geometry": Point(lon, lat)
        })

    if records:
        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
        gdf.to_file(out_geojson, driver='GeoJSON')
        gdf.to_file(shp_dir / f"{base_name}.shp")
        print(f"🛰️  [vector] Successfully exported {len(records)} fire pixels.")
