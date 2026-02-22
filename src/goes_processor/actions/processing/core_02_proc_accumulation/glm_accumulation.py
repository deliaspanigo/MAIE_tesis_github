# Version: v.0.5.4 (Core 02 - GLM Accumulation with Absolute Imports & Hourly Folders)

import sys
import time
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.ndimage import gaussian_filter
from pathlib import Path
from datetime import datetime
import rasterio
from rasterio.transform import from_origin

# IMPORT ABSOLUTO: Corrección para evitar ModuleNotFoundError
from goes_processor.actions.processing.core_01_proc_one_file.fdc import SmartIndentedOutput

# --- ORCHESTRATOR ---

def process_glm_heatmap_list_file(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    Main Orchestrator for GLM Accumulation.
    Structure: output / satellite / product / year / day / hour / time_bin / range / fn01
    """
    start_ts = time.time()
    
    # 1. CENTRALIZED PATH LOGIC (Extraído del primer archivo del lote)
    first_file = Path(file_list[0])
    parts = first_file.stem.split('_')
    
    # Time parsing from part 3: sYYYYJJJHHMMSS
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10] # Hora ancla para la carpeta
    
    sat_name = f"noaa-goes{satellite.replace('G', '')}"
    product_name = "GLM-L2-LCFA"
    
    def get_ts_short(p): return p.name.split('_')[3][1:14]
    folder_range = f"FROM_{get_ts_short(file_list[0])}_TO_{get_ts_short(file_list[-1])}"
    
    # Ruta raíz: output/sat/product/year/day/hour/time_bin/range_folder
    product_out_root = output_base / sat_name / product_name / year / day / hour / time_bin / folder_range
    
    # INITIALIZE REPORT FOR CLI COMPATIBILITY
    success_report = {"stage_01": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        print(f"⏰ [glm-accum] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Ejecutar Lógica de Acumulación
        success_report["stage_01"] = fn01_process_visuals(
            file_list, product_out_root, satellite, overwrite
        )
        
        duration = round((time.time() - start_ts) / 60, 2)
        print(f"✅ [glm-accum] Finished in {duration} min")
        return success_report

    except Exception as e:
        print(f"❌ [glm-accum] CRITICAL ERROR: {str(e)}")
        return success_report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr

# --- STAGE FUNCTIONS ---

def fn01_process_visuals(file_list, product_out_root: Path, satellite, overwrite=False):
    """
    Stage 01: GLM Accumulation Engine.
    Generates Gaussian Heatmap (GeoTIFF) and Visual Overlays (PNG).
    """
    fn_dir = product_out_root / "fn01"
    
    expected_files = {
        "transparent": fn_dir / "accumulated_wgs84_transparent.png",
        "geotiff": fn_dir / "accumulated_data.tif",
        "native": fn_dir / "accumulated_native_goes.png"
    }

    if not overwrite and all(f.exists() for f in expected_files.values()):
        print(f"✅ [fn01] Products already exist. Skipping.")
        return True

    fn_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"🧠 [fn01] Aggregating {len(file_list)} GLM files...")

        # 1. ACCUMULATION GRID (WGS84 0.1°)
        accumulated_grid = np.zeros((3600, 1800))
        all_lats, all_lons = [], []
        lon_edges = np.linspace(-180, 180, 3601)
        lat_edges = np.linspace(-90, 90, 1801)

        for f_path in file_list:
            try:
                with nc.Dataset(f_path, 'r') as ds:
                    lats = ds.variables['flash_lat'][:].flatten()
                    lons = ds.variables['flash_lon'][:].flatten()
                    if lats.size > 0:
                        lons = np.where(lons > 180, lons - 360, lons)
                        # Histograma 2D para acumular frecuencia de rayos
                        h_file, _, _ = np.histogram2d(lons, lats, bins=[lon_edges, lat_edges])
                        accumulated_grid += h_file
                        all_lats.extend(lats)
                        all_lons.extend(lons)
            except Exception as e:
                print(f"    ⚠️ Warning: Skipping {f_path.name}: {e}")

        # Aplicar filtro gaussiano para suavizado científico
        h_map = gaussian_filter(accumulated_grid.T, sigma=1.2)
        h_map_clean = np.where(h_map < 0.01, np.nan, h_map)

        # 2. EXPORT PRODUCTS
        
        # A. PNG Transparente (WGS84)
        print(f"📸 [fn01] Generating WGS84 Heatmap PNG...")
        fig_t = plt.figure(figsize=(20, 10), frameon=False)
        ax_t = plt.axes(projection=ccrs.PlateCarree())
        ax_t.set_axis_off()
        if len(all_lats) > 0:
            ax_t.imshow(h_map_clean, extent=[-180, 180, -90, 90], origin='lower', 
                        cmap='magma', transform=ccrs.PlateCarree())
        fig_t.savefig(expected_files["transparent"], transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig_t)

        # B. GeoTIFF Científico
        print(f"💾 [fn01] Exporting GeoTIFF Data...")
        transform = from_origin(-180, 90, 0.1, 0.1)
        with rasterio.open(expected_files["geotiff"], 'w', driver='GTiff', height=1800, width=3600, 
                           count=1, dtype='float32', crs='EPSG:4326', transform=transform, nodata=0) as dst:
            dst.write(np.flipud(np.nan_to_num(h_map_clean)).astype('float32'), 1)

        # C. Native Geostationary View
        print(f"🗺️  [fn01] Generating Native Full Disk View...")
        sat_lon = -75.0 if any(x in str(satellite) for x in ["16", "19"]) else -137.0
        goes_crs = ccrs.Geostationary(central_longitude=sat_lon)
        fig_g = plt.figure(figsize=(12, 12), facecolor='black')
        ax_g = plt.axes(projection=goes_crs)
        ax_g.set_global()
        try: ax_g.patch.set_facecolor('black')
        except: pass

        if all_lats:
            ax_g.scatter(all_lons, all_lats, color='orange', s=1, alpha=0.4, transform=ccrs.PlateCarree())
        fig_g.savefig(expected_files["native"], facecolor='black', edgecolor='none', bbox_inches='tight', dpi=150)
        plt.close(fig_g)

        return True

    except Exception as e:
        print(f"❌ [fn01] Error in accumulation logic: {str(e)}")
        return False
