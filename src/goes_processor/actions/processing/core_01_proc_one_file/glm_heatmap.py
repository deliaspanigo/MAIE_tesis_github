# src/goes_processor/actions/processing/core_01_proc_one_file/glm_heatmap.py
# Version: v.0.5.2 (GLM Heatmap - Path Refactoring with Hourly Folders & Dict Report)

import sys
import json
import warnings
import time
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter
from pathlib import Path
from datetime import datetime
import rasterio
from rasterio.transform import from_origin

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

def process_glm_heatmap_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Main Orchestrator for GLM Heatmap.
    Structure: output / satellite / product / year / day / hour / time_lapse / filename
    """
    start_ts = time.time()
    file_path = Path(input_file).resolve()
    base_name = file_path.stem
    
    # 1. CENTRALIZED PATH LOGIC (GOES-R Parsing)
    parts = base_name.split('_')
    sat_name = f"noaa-goes{parts[2].replace('G', '')}"
    product_clean = parts[1] # GLM-L2-LCFA

    # Time parsing from part 3: sYYYYJJJHHMMSS
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10]

    # Pre-calculated root directory (using 10min for GLM frequency consistency)
    product_out_root = output_base / sat_name / product_clean / year / day / hour / "time_lapse_20seconds" / base_name
    
    # INITIALIZE REPORT FOR CLI COMPATIBILITY
    success_report = {"stage_01": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        print(f"⏰ [glm] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Execute Stage 01
        success_report["stage_01"] = fn01_process_visuals(
            file_path, product_out_root, overwrite
        )
        
        duration = round((time.time() - start_ts) / 60, 2)
        print(f"✅ [glm] Finished in {duration} min")
        return success_report

    except Exception as e:
        print(f"❌ [glm] CRITICAL ERROR: {str(e)}")
        return success_report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr

# --- STAGE FUNCTIONS ---

def fn01_process_visuals(file_path: Path, product_out_root: Path, overwrite=False):
    """
    Stage 01: GLM Heatmap Generation.
    Includes: Standard Visuals, Scientific GeoTIFF, and Transparent Overlays.
    """
    start_ts = time.time()
    base_name = file_path.stem
    fn_dir = product_out_root / "fn01"
    
    # Check overwrite
    if not overwrite and (fn_dir / f"{base_name}_wgs84_transparent.png").exists():
        print(f"✅ [fn01] Skipping: Products already exist in {fn_dir.name}")
        return True

    fn_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Extraction & Cleaning
        print(f"📦 [fn01] [1/5] Extracting lightning flash data...")
        with nc.Dataset(file_path, 'r') as ds:
            lats = np.array(ds.variables['flash_lat'][:]).flatten()
            lons = np.array(ds.variables['flash_lon'][:]).flatten()
            mask = np.isfinite(lats) & np.isfinite(lons)
            lats, lons = lats[mask], lons[mask]
            lons = np.where(lons > 180, lons - 360, lons)

        # 2. Heatmap Logic
        print(f"🧠 [fn01] [2/5] Generating Gaussian Heatmap (sigma=3.0)...")
        lon_bins = np.linspace(-180, 180, 3601)
        lat_bins = np.linspace(-90, 90, 1801)
        heatmap, _, _ = np.histogram2d(lons, lats, bins=[lon_bins, lat_bins])
        h_map = gaussian_filter(heatmap.T, sigma=3.0)
        h_map = np.where(h_map < 0.001, np.nan, h_map)

        # 3. Product Generation: Standard Visuals (Black Background)
        print(f"📸 [fn01] [3/5] Exporting Standard PNG products...")
        
        # WGS84 Black
        fig_w = plt.figure(figsize=(20, 10), facecolor='black')
        ax_w = plt.axes(projection=ccrs.PlateCarree())
        ax_w.set_facecolor('black')
        ax_w.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=0.5)
        if lons.size > 0:
            ax_w.pcolormesh(lon_bins, lat_bins, h_map, cmap='magma', transform=ccrs.PlateCarree())
        fig_w.savefig(fn_dir / f"{base_name}_wgs84.png", facecolor='black', bbox_inches='tight', dpi=150)
        plt.close(fig_w)

        # Native Full Disk Black
        sat_lon = -75.0 if any(x in base_name for x in ["G16", "G19"]) else -137.0
        goes_crs = ccrs.Geostationary(central_longitude=sat_lon)
        fig_n = plt.figure(figsize=(12, 12), facecolor='black')
        ax_n = plt.axes(projection=goes_crs)
        ax_n.set_facecolor('black')
        ax_n.set_global()
        ax_n.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=0.8)
        if lons.size > 0:
            ax_n.scatter(lons, lats, color='orange', s=5, alpha=0.7, transform=ccrs.PlateCarree())
        fig_n.savefig(fn_dir / f"{base_name}_native_full_disk.png", facecolor='black', bbox_inches='tight', dpi=150)
        plt.close(fig_n)

        # 4. Transparent Overlays (Data Only)
        print(f"📸 [fn01] [4/5] Exporting Transparent Overlay products...")
        
        # WGS84 Transparent
        fig_wt = plt.figure(figsize=(20, 10), frameon=False)
        ax_wt = plt.axes(projection=ccrs.PlateCarree())
        ax_wt.set_axis_off()
        if lons.size > 0:
            ax_wt.pcolormesh(lon_bins, lat_bins, h_map, cmap='magma', transform=ccrs.PlateCarree())
        fig_wt.savefig(fn_dir / f"{base_name}_wgs84_transparent.png", transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig_wt)

        # Native Full Disk Transparent
        fig_nt = plt.figure(figsize=(12, 12), frameon=False)
        ax_nt = plt.axes(projection=goes_crs)
        ax_nt.set_axis_off()
        ax_nt.set_global()
        if lons.size > 0:
            ax_nt.scatter(lons, lats, color='orange', s=5, alpha=0.7, transform=ccrs.PlateCarree())
        fig_nt.savefig(fn_dir / f"{base_name}_native_transparent.png", transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig_nt)

        # 5. Scientific GeoTIFF & Metadata
        print(f"💾 [fn01] [5/5] Exporting Scientific GeoTIFF & JSON...")
        tif_path = fn_dir / f"{base_name}_data_wgs84.tif"
        transform = from_origin(-180, 0.1, 90, 0.1)
        data_to_save = np.flipud(np.nan_to_num(h_map))
        with rasterio.open(tif_path, 'w', driver='GTiff', height=1800, width=3600, count=1, 
                           dtype='float32', crs='EPSG:4326', transform=transform, nodata=0) as dst:
            dst.write(data_to_save.astype('float32'), 1)

        duration = round((time.time() - start_ts) / 60, 2)
        meta = {
            "source_file": base_name,
            "version": "v.0.5.2",
            "stage": "fn01",
            "flashes_count": int(lons.size),
            "duration_min": duration,
            "timestamp": datetime.now().isoformat()
        }
        with open(fn_dir / f"{base_name}_metadata_fn01.json", 'w') as f:
            json.dump(meta, f, indent=4)

        print(f"✅ [fn01] Stage complete.")
        return True

    except Exception as e:
        print(f"❌ [fn01] Error in visual processing: {str(e)}")
        return False
