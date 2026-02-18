# Version: v.0.4.9 (Core 02 - FDC Accumulation Satpy Native)

import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import rasterio
from rasterio.transform import from_origin

# Reutilizamos tu capturador de logs para mantener la indentación
from ..core_01_proc_one_file.fdc import SmartIndentedOutput

def fn01_fdc_accumulation_logic(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    Core 02 - Stage 01: FDC Fire Persistence.
    Carga múltiples archivos usando Satpy y suma las detecciones de fuego en una malla WGS84.
    """
    start_ts = time.time()
    report = {"fdc_accum": False}
    
    # Redirección de logs para el CLI
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # --- 1. CONSTRUCCIÓN DE RUTAS ---
        def get_ts(p): return p.name.split('_')[3][1:14]
        first_ts, last_ts = get_ts(file_list[0]), get_ts(file_list[-1])
        year, day = first_ts[:4], first_ts[4:7]
        sat_folder = f"noaa-goes{satellite.replace('G', '')}"
        folder_range = f"{first_ts}_TO_{last_ts}"
        
        # Carpeta de salida siguiendo tu estructura de fn01
        fn_dir = (output_base / "core02" / sat_folder / "ABI-L2-FDCF" / 
                  year / day / time_bin / folder_range / "fn01")

        out_png = fn_dir / "fdc_persistence_wgs84.png"
        out_tif = fn_dir / "fdc_persistence_data.tif"

        if not overwrite and out_png.exists():
            print(f"✅ [fn01] Accumulated FDC products already exist. Skipping.")
            report["fdc_accum"] = True
            return report

        fn_dir.mkdir(parents=True, exist_ok=True)
        
        # --- 2. CONFIGURACIÓN DE ÁREA (WGS84 0.1°) ---
        area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 
                                  3600, 1800, [-180, -90, 180, 90])
        
        # Matriz para acumular las detecciones
        persistence_grid = np.zeros((1800, 3600))
        
        # IDs de fuego que usas en tu fn03 vectorial
        fire_ids = [10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35]

        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        print(f"🧠 [1/3] Merging {len(file_list)} FDC Scenes into Persistence Grid...")

        # --- 3. BUCLE DE ACUMULACIÓN ---
        for f_path in file_list:
            try:
                # Cargamos la escena usando tu reader 'abi_l2_nc'
                scn = Scene(filenames=[str(f_path)], reader='abi_l2_nc')
                
                # Cargamos tu composite de análisis (fn03)
                scn.load(['my_fdc_fn03'])
                
                # Remuestreamos a la malla común para poder sumar los píxeles
                scn_res = scn.resample(area_def, resampler='kd_tree')
                data = scn_res['my_fdc_fn03'].values
                
                # Creamos máscara de fuego y sumamos a la persistencia
                fire_mask = np.isin(data, fire_ids).astype(int)
                persistence_grid += fire_mask
                
            except Exception as e:
                print(f"    ⚠️ Warning: Could not process {f_path.name}: {e}")

        # --- 4. EXPORTACIÓN DE PRODUCTOS ---
        
        # A. PNG de Persistencia (Visual)
        print(f"📸 [2/3] Generating Persistence Heatmap...")
        plt.figure(figsize=(20, 10), frameon=False)
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_axis_off()
        
        p_clean = np.where(persistence_grid == 0, np.nan, persistence_grid)
        if not np.all(np.isnan(p_clean)):
            ax.imshow(p_clean, extent=[-180, 180, -90, 90], 
                      origin='upper', cmap='YlOrRd', transform=ccrs.PlateCarree())
        
        plt.savefig(out_png, transparent=True, bbox_inches='tight', pad_inches=0, dpi=150)
        plt.close()

        # B. GeoTIFF Científico
        print(f"💾 [3/3] Exporting Data GeoTIFF...")
        transform = from_origin(-180, 90, 0.1, 0.1)
        with rasterio.open(
            out_tif, 'w', driver='GTiff', height=1800, width=3600, 
            count=1, dtype='float32', crs='EPSG:4326', transform=transform, nodata=0
        ) as dst:
            dst.write(persistence_grid.astype('float32'), 1)

        report["fdc_accum"] = True
        return report

    except Exception as e:
        print(f"❌ ERROR in FDC Accumulation: {str(e)}")
        return report
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr

def process_fdc_accumulation_list(file_list, output_base, time_bin, satellite, overwrite=False, indent=""):
    """
    Orquestador para Core 02 - ABI-L2-FDCF.
    Llamado directamente por el CLI.
    """
    res = fn01_fdc_accumulation_logic(
        file_list=file_list, 
        output_base=output_base, 
        time_bin=time_bin, 
        satellite=satellite, 
        overwrite=overwrite, 
        indent=indent
    )
    # Retornamos el formato de reporte que espera tu CLI
    return {"fn01": res["fdc_accum"]}
