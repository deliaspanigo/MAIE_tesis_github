# Version: v.0.4.5 (FDC Orchestrator - Fixed Class Definition & Overwrite)

import sys
import yaml
import warnings
import numpy as np
import time
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
                # No indentar si la línea empieza con un icono de estado
                if not any(icon in line for icon in ["⏰", "📁", "📂", "🧠", "📦", "📸", "🗺️", "🔄", "💾", "✅", "🏁", "⏱️", "❌", "🛰️"]):
                    self.original_stream.write(self.base_indent + self.extra_indent + line)
                else:
                    self.original_stream.write(self.base_indent + line)
            else:
                self.original_stream.write(line)
            self.newline = line.endswith('\n')

    def flush(self):
        self.original_stream.flush()

# --- UTILS ---

def fn_get_color_scale_config(enhancement_name):
    """Dynamically fetches color scales from Satpy YAML config."""
    try:
        for search_path in satpy_config.get("config_path", []):
            potential_file = Path(search_path) / "enhancements" / "abi.yaml"
            if potential_file.exists():
                with open(potential_file, 'r') as f:
                    conf = yaml.unsafe_load(f)
                palette = conf['enhancements'][enhancement_name]['operations'][0]['kwargs']['palettes'][0]
                return palette
    except Exception: pass
    return None

# --- STAGES ---

def fn01_process_visuals(scn, main_out_dir, base_name, overwrite=False):
    """FN01: Standard visual masks (Solid PNG & GeoTIFF)."""
    fn_dir = main_out_dir / "fn01"
    out_png = fn_dir / f"{base_name}_fn01_wgs84.png"
    
    if not overwrite and out_png.exists():
        print(f"✅ [fn01] Products already exist. Skipping.")
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
        return scn.resample(area_def, resampler='kd_tree')

    fn_dir.mkdir(parents=True, exist_ok=True)
    print(f"🧠 [fn01] Applying visual mask transparency logic...")
    data = scn['my_fdc_fn01']
    data_filled = data.where(~np.isnan(data), 40).where(data != 127, 40)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn01'] = data_filled

    print(f"📸 [fn01] Saving native projection plot...")
    get_enhanced_image(scn['my_fdc_fn01']).convert("RGB").save(str(fn_dir / f"{base_name}_fn01_native.png"))

    print(f"🗺️  [fn01] Resampling to WGS84 (EPSG:4326)...")
    area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
    scn_res = scn.resample(area_def, resampler='kd_tree')

    print(f"💾 [fn01] Exporting WGS84 products...")
    get_enhanced_image(scn_res['my_fdc_fn01']).convert("RGB").save(str(out_png))
    scn_res.save_dataset('my_fdc_fn01', filename=str(fn_dir / f"{base_name}_fn01_wgs84.tif"), writer='geotiff')
    return scn_res

def fn02_process_analysis(scn, scn_res, main_out_dir, base_name, overwrite=False):
    """FN02: Data analysis plots (Dark Ramp)."""
    fn_dir = main_out_dir / "fn02"
    out_png = fn_dir / f"{base_name}_fn02_wgs84.png"

    if not overwrite and out_png.exists():
        print(f"✅ [fn02] Analysis products already exist. Skipping.")
        return

    fn_dir.mkdir(parents=True, exist_ok=True)
    print(f"🧠 [fn02] Applying analysis transparency logic...")
    data = scn['my_fdc_fn02']
    data_filled = data.where(~np.isnan(data), 127).where(data != 127, 127)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn02'] = data_filled

    print(f"📸 [fn02] Saving native plot (Analysis Ramp)...")
    get_enhanced_image(scn['my_fdc_fn02']).convert("RGB").save(str(fn_dir / f"{base_name}_fn02_native.png"))

    print(f"💾 [fn02] Saving WGS84 analysis products...")
    get_enhanced_image(scn_res['my_fdc_fn02']).convert("RGB").save(str(out_png))
    scn_res.save_dataset('my_fdc_fn02', filename=str(fn_dir / f"{base_name}_fn02_wgs84.tif"), writer='geotiff')

def fn03_process_vectorial(scn, scn_res, main_out_dir, base_name, overwrite=False):
    """FN03: Clustering and Vector export (GeoJSON, SHP)."""
    fn_dir = main_out_dir / "fn03"
    vector_dir = fn_dir / "vectorial"
    out_geojson = vector_dir / f"{base_name}.geojson"

    if not overwrite and out_geojson.exists():
        print(f"✅ [fn03] Vectorial products already exist. Skipping.")
        return

    shp_dir = vector_dir / "shapefile"
    for d in [fn_dir, vector_dir, shp_dir]: d.mkdir(parents=True, exist_ok=True)
    
    print(f"🧠 [fn03] Starting Full Analytics & Vector Export...")
    get_enhanced_image(scn['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_fn03_native.png"))
    get_enhanced_image(scn_res['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_fn03_wgs84.png"))

    fire_ids = [10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35]
    data_vals = scn_res['my_fdc_fn03'].values
    fire_mask = np.isin(data_vals, fire_ids)
    
    if not np.any(fire_mask):
        print(f"🏁 [fn03] No fire pixels detected. Vector export skipped.")
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

# --- ORCHESTRATOR ---

def process_fdc_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """FDC Orchestrator v0.4.5"""
    start_ts = time.time()
    report = {"fn01": False, "fn02": False, "fn03": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        file_path = Path(input_file).resolve()
        base_name = file_path.stem
        rel_path = file_path.relative_to(input_base.resolve())
        main_out_dir = output_base / rel_path.parent / base_name
        
        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['my_fdc_fn01', 'my_fdc_fn02', 'my_fdc_fn03'])

        scn_res = fn01_process_visuals(scn, main_out_dir, base_name, overwrite=overwrite)
        report["fn01"] = True
        
        fn02_process_analysis(scn, scn_res, main_out_dir, base_name, overwrite=overwrite)
        report["fn02"] = True
        
        fn03_process_vectorial(scn, scn_res, main_out_dir, base_name, overwrite=overwrite)
        report["fn03"] = True
        
        print(f"✅ Finished in {round((time.time()-start_ts)/60, 2)} min")
        return report

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
