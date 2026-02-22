# Version: v.0.5.3 (Core 02 - FDC Accumulation with Hourly Folders & Sync Paths)

import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import rasterio
from rasterio.transform import from_origin

# Importamos tu capturador de logs para mantener la indentación
# Nota: Asegúrate de que la ruta de importación sea correcta según tu estructura
# from ...core_01_proc_one_file.fdc import SmartIndentedOutput
from goes_processor.actions.processing.core_01_proc_one_file.fdc import SmartIndentedOutput
# --- ORCHESTRATOR ---

def process_fdc_accumulation_list(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    Main Orchestrator for Core 02 - FDC Accumulation.
    Structure: output / satellite / product / year / day / hour / time_bin / range / fn01
    """
    start_ts = time.time()
    
    # 1. CENTRALIZED PATH LOGIC (Parsed from the first file of the batch)
    first_file = Path(file_list[0])
    parts = first_file.stem.split('_')
    
    # Time parsing from part 3: sYYYYJJJHHMMSS
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10] # Using the hour of the first file as anchor
    
    sat_name = f"noaa-goes{satellite.replace('G', '')}"
    product_name = "ABI-L2-FDCF" # Fixed for FDC Accumulation
    
    # Create a time range string for the folder name
    def get_ts_short(p): return p.name.split('_')[3][1:14]
    folder_range = f"FROM_{get_ts_short(file_list[0])}_TO_{get_ts_short(file_list[-1])}"
    
    # Final Root Path
    # output/sat/product/year/day/hour/time_bin/range_folder
    product_out_root = output_base / sat_name / product_name / year / day / hour / time_bin / folder_range
    
    # INITIALIZE REPORT FOR CLI COMPATIBILITY
    success_report = {"stage_01": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        print(f"⏰ [fdc-accum] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Execute Logic
        success_report["stage_01"] = fn01_fdc_accumulation_logic(
            file_list, product_out_root, overwrite
        )
        
        duration = round((time.time() - start_ts) / 60, 2)
        print(f"✅ [fdc-accum] Finished in {duration} min")
        return success_report

    except Exception as e:
        print(f"❌ [fdc-accum] CRITICAL ERROR: {str(e)}")
        return success_report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr

# --- STAGE FUNCTIONS ---

def fn01_fdc_accumulation_logic(file_list, product_out_root: Path, overwrite=False):
    """
    Stage 01: FDC Fire Persistence Grid.
    Loads multiple files using Satpy and sums fire detections into a WGS84 grid.
    """
    fn_dir = product_out_root / "fn01"
    out_png = fn_dir / "fdc_persistence_wgs84.png"
    out_tif = fn_dir / "fdc_persistence_data.tif"

    if not overwrite and out_png.exists():
        print(f"✅ [fn01] Accumulated FDC products already exist. Skipping.")
        return True

    fn_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. GRID DEFINITION (WGS84 0.1°)
    area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 
                              3600, 1800, [-180, -90, 180, 90])
    
    persistence_grid = np.zeros((1800, 3600))
    fire_ids = [10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35]

    print(f"🧠 [fn01] Merging {len(file_list)} Scenes into Persistence Grid...")

    # 2. ACCUMULATION LOOP
    for f_path in file_list:
        try:
            scn = Scene(filenames=[str(f_path)], reader='abi_l2_nc')
            scn.load(['my_fdc_fn03'])
            
            # Resample to common grid
            scn_res = scn.resample(area_def, resampler='kd_tree')
            data = scn_res['my_fdc_fn03'].values
            
            # Mask and Sum
            fire_mask = np.isin(data, fire_ids).astype(int)
            persistence_grid += fire_mask
            
        except Exception as e:
            print(f"    ⚠️ Warning: Skipping {f_path.name}: {e}")

    # 3. EXPORT PRODUCTS
    
    # A. PNG Heatmap
    print(f"📸 [fn01] Generating Persistence Heatmap...")
    plt.figure(figsize=(20, 10), frameon=False)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_axis_off()
    
    p_clean = np.where(persistence_grid == 0, np.nan, persistence_grid)
    if not np.all(np.isnan(p_clean)):
        ax.imshow(p_clean, extent=[-180, 180, -90, 90], 
                  origin='upper', cmap='YlOrRd', transform=ccrs.PlateCarree())
    
    plt.savefig(out_png, transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    # B. Scientific GeoTIFF
    print(f"💾 [fn01] Exporting Data GeoTIFF...")
    transform = from_origin(-180, 90, 0.1, 0.1)
    with rasterio.open(
        out_tif, 'w', driver='GTiff', height=1800, width=3600, 
        count=1, dtype='float32', crs='EPSG:4326', transform=transform, nodata=0
    ) as dst:
        dst.write(persistence_grid.astype('float32'), 1)

    return True
