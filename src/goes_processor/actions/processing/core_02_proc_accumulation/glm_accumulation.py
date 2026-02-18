# Version: v.0.4.6 (Core 02 Accumulation - Orchestrator Pattern)

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

# Reutilizamos la clase para mantener el estilo de indentación en los logs
from ..core_01_proc_one_file.glm_heatmap import SmartIndentedOutput

def fn01_process_visuals(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    Core 02 - Stage 01: GLM Accumulation Engine.
    Genera heatmap científico (GeoTIFF) y visuales (PNG).
    """
    start_ts = time.time()
    report = {"glm_accum": False}
    
    # Redirección de logs
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        if not file_list:
            print("❌ Error: No files provided for accumulation.")
            return report

        # --- 1. RECONSTRUCCIÓN DE RUTAS ---
        def get_ts(p): return p.name.split('_')[3][1:14]
        
        first_ts, last_ts = get_ts(file_list[0]), get_ts(file_list[-1])
        year, day = first_ts[:4], first_ts[4:7]
        sat_folder = f"noaa-goes{satellite.replace('G', '')}"
        
        folder_range = f"{first_ts}_TO_{last_ts}"
        # Estructura corregida para seguir el patrón de "fn01"
        fn_dir = (output_base / "core02" / sat_folder / "GLM-L2-LCFA" / 
                  year / day / time_bin / folder_range / "fn01")

        expected_files = [
            fn_dir / "accumulated_wgs84_transparent.png",
            fn_dir / "accumulated_data.tif",
            fn_dir / "accumulated_native_goes.png"
        ]

        if not overwrite and all(f.exists() for f in expected_files):
            print(f"✅ Products already exist (fn01). Skipping.")
            report["glm_accum"] = True
            return report

        fn_dir.mkdir(parents=True, exist_ok=True)

        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        print(f"🧠 [1/4] Aggregating {len(file_list)} files...")

        # --- 2. LÓGICA DE ACUMULACIÓN ---
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
                        h_file, _, _ = np.histogram2d(lons, lats, bins=[lon_edges, lat_edges])
                        accumulated_grid += h_file
                        all_lats.extend(lats)
                        all_lons.extend(lons)
            except Exception as e:
                print(f"    ⚠️ Warning: Could not read {f_path.name}: {e}")

        h_map = gaussian_filter(accumulated_grid.T, sigma=1.2)
        h_map_clean = np.where(h_map < 0.01, np.nan, h_map)

        # --- 3. EXPORTACIÓN ---
        # PNG Transparente
        print(f"📸 [2/4] Generating WGS84 PNG...")
        fig_t = plt.figure(figsize=(20, 10), frameon=False)
        ax_t = plt.axes(projection=ccrs.PlateCarree())
        ax_t.set_axis_off()
        if len(all_lats) > 0:
            ax_t.imshow(h_map_clean, extent=[-180, 180, -90, 90], origin='lower', 
                        cmap='magma', transform=ccrs.PlateCarree())
        fig_t.savefig(expected_files[0], transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close(fig_t)

        # GeoTIFF
        print(f"💾 [3/4] Exporting GeoTIFF...")
        transform = from_origin(-180, 90, 0.1, 0.1)
        with rasterio.open(expected_files[1], 'w', driver='GTiff', height=1800, width=3600, 
                           count=1, dtype='float32', crs='EPSG:4326', transform=transform, nodata=0) as dst:
            dst.write(np.flipud(np.nan_to_num(h_map_clean)).astype('float32'), 1)

        # Native View
        print(f"🗺️  [4/4] Generating Native View...")
        sat_lon = -75.0 if satellite in ["G16", "G19"] else -137.0
        goes_crs = ccrs.Geostationary(central_longitude=sat_lon)
        fig_g = plt.figure(figsize=(12, 12), facecolor='black')
        ax_g = plt.axes(projection=goes_crs)
        ax_g.set_global()
        try: ax_g.patch.set_facecolor('black')
        except: pass

        if all_lats:
            ax_g.scatter(all_lons, all_lats, color='orange', s=1, alpha=0.4, transform=ccrs.PlateCarree())
        fig_g.savefig(expected_files[2], facecolor='black', edgecolor='none', bbox_inches='tight', dpi=150)
        plt.close(fig_g)

        report["glm_accum"] = True
        return report

    except Exception as e:
        print(f"❌ ERROR in fn01: {str(e)}")
        return report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr


def process_glm_heatmap_list_file(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    GLM Accumulation Orchestrator v0.4.6
    Maneja la ejecución secuencial de etapas de acumulación.
    """
    start_ts = time.time()
    report = {"fn01": False}
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # Ejecutar Etapa 1: Visuales y GeoTIFF
        scn_res = fn01_process_visuals(
            file_list=file_list, 
            output_base=output_base, 
            time_bin=time_bin, 
            satellite=satellite, 
            overwrite=overwrite, 
            indent=indent
        )
        
        report["fn01"] = scn_res["glm_accum"]
        
        print(f"✅ Finished Accumulation in {round((time.time()-start_ts)/60, 2)} min")
        return report

    except Exception as e:
        print(f"❌ ERROR in Orchestrator Core 02: {str(e)}")
        return report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
