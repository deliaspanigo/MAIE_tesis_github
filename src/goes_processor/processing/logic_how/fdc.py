# src/goes_processor/processing/logic_how/fdcf.py
# Version: v.0.0.1 (Fixed Path Input)

import sys
import json
import yaml
import warnings
import numpy as np
import time
import os
import pandas as pd # Asegúrate de tener pandas importado al inicio del archivo
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition
from satpy.enhancements.enhancer import get_enhanced_image

warnings.filterwarnings("ignore")

# 

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

# --- UTILS ---

def fn_get_color_scale_config(enhancement_name):
    """Dynamically fetches the color scale from the Satpy YAML config."""
    try:
        for search_path in satpy_config.get("config_path", []):
            potential_file = Path(search_path) / "enhancements" / "abi.yaml"
            if potential_file.exists():
                with open(potential_file, 'r') as f:
                    conf = yaml.unsafe_load(f)
                palette = conf['enhancements'][enhancement_name]['operations'][0]['kwargs']['palettes'][0]
                return {
                    "values": palette['values'],
                    "colors": palette['colors'],
                    "source_yml": str(potential_file)
                }
    except Exception: pass
    return None

# --- SUB-PROCESS 01 (Standard Visuals) ---

def fn01_process_visuals(scn, main_out_dir, base_name, start_ts):
    """FN01: Generates visual products using my_fdc_fn01 color ramp."""
    fn_dir = main_out_dir / "fn01"
    fn_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🧠 [fn01] Applying transparency logic for Visual Mask...")
    # Asegurar que cargamos el dataset correcto
    data = scn['my_fdc_fn01']
    data_filled = data.where(~np.isnan(data), 40).where(data != 127, 40)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn01'] = data_filled

    scale = fn_get_color_scale_config('my_fdc_fn01')
    if scale:
        with open(fn_dir / f"{base_name}_fn01_colors.yml", 'w') as yf:
            yaml.dump({"fn01_visual_scale": scale}, yf)

    print(f"📸 [fn01] Saving native solid PNG...")
    get_enhanced_image(scn['my_fdc_fn01']).convert("RGB").save(str(fn_dir / f"{base_name}_fn01_native.png"))

    print(f"🗺️  [fn01] Resampling to WGS84...")
    area_def = AreaDefinition('wgs84', 'Global', 'epsg4326', 'EPSG:4326', 3600, 1800, [-180, -90, 180, 90])
    scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=satpy_config.get("cache_dir"))

    print(f"💾 [fn01] Saving WGS84 PNG & GeoTIFF...")
    get_enhanced_image(scn_res['my_fdc_fn01']).convert("RGB").save(str(fn_dir / f"{base_name}_fn01_wgs84.png"))
    scn_res.save_dataset('my_fdc_fn01', filename=str(fn_dir / f"{base_name}_fn01_wgs84.tif"), writer='geotiff')

    with open(fn_dir / f"{base_name}_fn01_metadata.json", 'w') as f:
        json.dump({"step": "fn01", "generated_files": [f.name for f in fn_dir.glob("*")]}, f, indent=4)

    return scn_res

# --- SUB-PROCESS 02 (New Color Ramp / Analysis) ---

def fn02_process_analysis(scn, scn_res, main_out_dir, base_name, start_ts):
    """FN02: Generates visual products using my_fdc_fn02 (New Dark Ramp)."""
    fn_dir = main_out_dir / "fn02"
    fn_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🧠 [fn02] Applying transparency logic for Analysis Mask...")
    data = scn['my_fdc_fn02']
    data_filled = data.where(~np.isnan(data), 127).where(data != 127, 127)
    for attr in ['_FillValue', 'valid_range']:
        if attr in data_filled.attrs: del data_filled.attrs[attr]
    scn['my_fdc_fn02'] = data_filled

    scale = fn_get_color_scale_config('my_fdc_fn02')
    if scale:
        with open(fn_dir / f"{base_name}_fn02_colors.yml", 'w') as yf:
            yaml.dump({"fn02_analysis_scale": scale}, yf)

    print(f"📸 [fn02] Saving native solid PNG (New Ramp)...")
    get_enhanced_image(scn['my_fdc_fn02']).convert("RGB").save(str(fn_dir / f"{base_name}_fn02_native.png"))

    print(f"💾 [fn02] Saving WGS84 PNG & GeoTIFF (New Ramp)...")
    get_enhanced_image(scn_res['my_fdc_fn02']).convert("RGB").save(str(fn_dir / f"{base_name}_fn02_wgs84.png"))
    scn_res.save_dataset('my_fdc_fn02', filename=str(fn_dir / f"{base_name}_fn02_wgs84.tif"), writer='geotiff')

    data_vals = scn_res['my_fdc_fn02'].values
    unique, counts = np.unique(data_vals[~np.isnan(data_vals)], return_counts=True)
    stats = {int(u): int(c) for u, c in zip(unique, counts)}

    with open(fn_dir / f"{base_name}_fn02_metadata.json", 'w') as f:
        json.dump({"step": "fn02", "pixel_counts": stats, "generated_files": [f.name for f in fn_dir.glob("*")]}, f, indent=4)


# --- SUB-PROCESS 02 (New Color Ramp / Analysis) ---




import pandas as pd
import numpy as np
import yaml
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path
from scipy.ndimage import label
from shapely.geometry import Point
import geopandas as gpd
from satpy.enhancements.enhancer import get_enhanced_image

def fn03_process_analysis(scn, scn_res, main_out_dir, base_name, start_ts):
    """
    FN03: Genera visuales y estructura vectorial (GeoJSON, KML, KMZ, Shapefile).
    v.0.0.1 - Incluye Clustering, WKT y base de datos de píxeles.
    """
    # 1. PREPARACIÓN DE DIRECTORIOS
    fn_dir = main_out_dir / "fn03"
    vector_dir = fn_dir / "vectorial"
    shp_dir = vector_dir / "shapefile"
    
    for d in [fn_dir, vector_dir, shp_dir]: 
        d.mkdir(parents=True, exist_ok=True)
    
    print(f"🧠 [fn03] Starting Full Analytics & Vector Export...")

    # 2. CONFIGURACIÓN Y COLORES
    # Buscamos la función de escala en el contexto global para evitar errores de importación
    fn_get_color_scale_config = globals().get('fn_get_color_scale_config')
    
    if fn_get_color_scale_config:
        scale = fn_get_color_scale_config('my_fdc_fn03')
        if scale:
            with open(fn_dir / f"{base_name}_fn03_colors.yml", 'w') as yf:
                yaml.dump({"fn03_analysis_scale": scale}, yf)

    # 3. IMÁGENES Y GEOTIFF
    print(f"📸 [fn03] Saving Transparent PNGs & GeoTIFF...")
    get_enhanced_image(scn['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_fn03_native.png"))
    get_enhanced_image(scn_res['my_fdc_fn03']).convert("RGBA").save(str(fn_dir / f"{base_name}_fn03_wgs84.png"))
    scn_res.save_dataset('my_fdc_fn03', filename=str(fn_dir / f"{base_name}_fn03_wgs84.tif"), writer='geotiff')

    # 4. EXTRACCIÓN DE DATOS, CLUSTERING Y WKT
    fire_ids = [10, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35]
    data_vals = scn_res['my_fdc_fn03'].values
    
    # Identificar píxeles de fuego y agruparlos (Conectividad de 8 vecinos)
    fire_mask = np.isin(data_vals, fire_ids)
    labeled_array, num_features = label(fire_mask, structure=np.ones((3, 3)))
    
    lons, lats = scn_res['my_fdc_fn03'].attrs['area'].get_lonlats()
    records = []
    
    y_idx, x_idx = np.where(fire_mask)
    for r, c in zip(y_idx, x_idx):
        lat, lon = round(float(lats[r, c]), 6), round(float(lons[r, c]), 6)
        records.append({
            "source_file": f"{base_name}.nc",
            "fdcf_id": int(data_vals[r, c]),
            "latitude": lat,
            "longitude": lon,
            "wkt": f"POINT({lon} {lat})",
            "cluster_id": int(labeled_array[r, c]),
            "pixel_row": int(r),
            "pixel_col": int(c),
            "geometry": Point(lon, lat)
        })

    # 5. GENERACIÓN DE PRODUCTOS TABULARES Y VECTORIALES
    if records:
        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
        
        # A. Guardar CSV (Tabular)
        df_csv = gdf.drop(columns=["geometry"]).copy()
        df_csv.insert(0, 'order_id', range(1, len(df_csv) + 1))
        df_csv.to_csv(fn_dir / f"{base_name}_fn03_fire_database.csv", index=False)

        # B. Guardar GeoJSON (Fácil de leer y estándar)
        print(f"🛰️  [vector] Generating GeoJSON...")
        gdf.to_file(vector_dir / f"{base_name}.geojson", driver='GeoJSON')

        # C. Guardar Shapefile (Carpeta aislada)
        print(f"🛰️  [vector] Generating Shapefile...")
        gdf.to_file(shp_dir / f"{base_name}.shp")

        # D. Guardar KML/KMZ (Con manejo de errores si falta Fiona)
        print(f"🛰️  [vector] Attempting KML/KMZ export...")
        kml_path = vector_dir / f"{base_name}.kml"
        try:
            import fiona
            fiona.drvsupport.supported_drivers['KML'] = 'rw'
            fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
            # Exportamos solo columnas básicas para evitar errores de formato KML
            gdf[['fdcf_id', 'cluster_id', 'geometry']].to_file(kml_path, driver='KML')
            
            # Comprimir a KMZ
            with zipfile.ZipFile(vector_dir / f"{base_name}.kmz", 'w') as kmz:
                kmz.write(kml_path, arcname="doc.kml")
        except (ImportError, Exception) as e:
            print(f"⚠️  KML/KMZ export skipped: {e}")

        fire_summary = df_csv['fdcf_id'].value_counts().to_dict()
    else:
        print(f"⚠️  [fn03] No fire pixels detected in this scene.")
        fire_summary = {}

    # 6. METADATOS FINALES
    with open(fn_dir / f"{base_name}_fn03_metadata.json", 'w') as f:
        json.dump({
            "step": "fn03_vectorial",
            "fires_found": len(records),
            "clusters": int(num_features),
            "duration_sec": round(time.time() - start_ts, 2)
        }, f, indent=4)
# --- MASTER PROCESSOR ---

# --- MASTER PROCESSOR ---

def process_file(input_file, input_base: Path, output_base: Path, format="both", overwrite=False, indent=""):
    """Orchestrator v.0.0.1 (Fixed input for lists)"""
    start_time = datetime.now()
    start_ts = time.time()
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # --- FIX: Convert list to single Path ---
        if isinstance(input_file, list):
            input_file = input_file[0]
        
        file_path = Path(input_file).resolve()
        base_name = file_path.stem
        
        # Resolve relative path for directory structure
        rel_path = file_path.relative_to(input_base.resolve())
        main_out_dir = output_base / rel_path.parent / base_name
        main_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"⏰ Start: {start_time.strftime('%H:%M:%S')}")
        print(f"📁 Source: {file_path.name}")
        
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['my_fdc_fn01', 'my_fdc_fn02', 'my_fdc_fn03'])

        # Execute FN01
        scn_res = fn01_process_visuals(scn, main_out_dir, base_name, start_ts)
        
        # Execute FN02
        fn02_process_analysis(scn, scn_res, main_out_dir, base_name, start_ts)
        
        # Execute FN03
        fn03_process_analysis(scn, scn_res, main_out_dir, base_name, start_ts)
        
        print(f"🏁 End: {datetime.now().strftime('%H:%M:%S')} | ⏱️ {round((time.time()-start_ts)/60, 2)} min")
        with open(main_out_dir / f"{base_name}_summary.json", 'w') as f:
            json.dump({"version": "v.0.0.1", "steps": ["fn01", "fn02", "fn03"]}, f, indent=4)

        return main_out_dir

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise e
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
