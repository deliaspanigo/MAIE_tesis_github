# Version: v.0.5.0 (MCMIP Orchestrator - Path Refactoring with Hourly Folders)
import sys
import json
import warnings
import time
import os
import matplotlib
# Force non-interactive backend to prevent Tcl/Tkinter thread errors in CLI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

warnings.filterwarnings("ignore")

import os
import warnings
import logging

# Bloqueo a nivel de variable de entorno (algunas librerías de C lo leen)
os.environ['PYTHONWARNINGS'] = 'ignore:No sensor name specified'

# Filtros de Python
warnings.filterwarnings("ignore", message=".*No sensor name specified.*")
logging.getLogger("satpy").setLevel(logging.ERROR)



class SmartIndentedOutput:
    """
    Captures output and applies double indentation for library logs.
    FILTRO V.0.5.1: Bloquea activamente el aviso de 'No sensor name'.
    """
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "
        self.newline = True

    def write(self, text):
        # --- FILTRO CRÍTICO ---
        # Si el texto contiene el aviso del sensor, lo ignoramos por completo
        if "No sensor name specified" in text:
            return 
        # ----------------------

        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                # Detectamos si es una línea de nuestro orquestador (con iconos) o de una librería
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

def apply_dark_transparency(input_path: Path, output_path: Path, threshold=15):
    """
    Lee un PNG, identifica píxeles por debajo del umbral de brillo y los vuelve transparentes.
    """
    from PIL import Image  # <--- IMPORT LOCAL PARA EVITAR EL ERROR
    import numpy as np     # <--- IMPORT LOCAL SEGURO
    
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    
    # Calculamos el brillo promedio de los canales R, G, B
    rgb = data[:, :, :3]
    brightness = np.mean(rgb, axis=2)
    
    # Máscara: Píxeles donde el brillo es muy bajo (espacio exterior)
    dark_pixels = brightness <= threshold
    
    # Cambiamos el canal Alfa (índice 3) a 0 para esos píxeles
    data[dark_pixels, 3] = 0
    
    # Guardar resultado
    Image.fromarray(data).save(output_path)
    
    
def apply_grayscale_transparency(input_path: Path, output_path: Path, saturation_threshold=20):
    """
    Lee un PNG de nubes colorizadas y vuelve transparente todo lo que sea escala de grises.
    Basado en la diferencia entre canales (R, G, B).
    """
    from PIL import Image
    import numpy as np
    
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    
    rgb = data[:, :, :3].astype(np.int16)
    
    # Calculamos la diferencia máxima entre canales (Saturación simple)
    # En un gris puro, R=G=B, por lo que diff = 0.
    max_val = np.max(rgb, axis=2)
    min_val = np.min(rgb, axis=2)
    diff = max_val - min_val
    
    # Píxeles donde la diferencia de color es muy baja (son grises)
    gray_pixels = diff <= saturation_threshold
    
    # Canal Alfa a 0 para los grises
    data[gray_pixels, 3] = 0
    
    Image.fromarray(data).save(output_path)
    

def process_mcmip_true_color_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Main Orchestrator for MCMIP Module.
    Structure: output / satellite / product / year / day / hour / time_lapse / filename
    Executes Stage 01 (True Color) and Stage 02 (Colorized IR).
    """
    file_path = Path(input_file).resolve()
    base_name = file_path.stem
    
    # 1. ROBUST PATH LOGIC (GOES-R Parsing)
    parts = base_name.split('_')
    # noaa-goes19, noaa-goes18, etc.
    sat_name = f"noaa-goes{parts[2].replace('G', '')}"
    
    # Robust product name extraction (protecting internal 'M')
    product_raw = parts[1]
    product_clean = product_raw.rsplit('-M', 1)[0] if '-M' in product_raw else product_raw

    # Time parsing from part 3: sYYYYJJJHHMMSS
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10] # Extracting HH (Hour)

    # Pre-calculated root directory including HOUR
    # Path: output/sat/product/year/day/hour/time_lapse_10minutes/base_name
    product_out_root = output_base / sat_name / product_clean / year / day / hour / "time_lapse_10minutes" / base_name
    
    success_report = {"stage_01": False, "stage_02": False}
    
    # --- EXECUTION PIPELINE ---

    # Stage 01: True Color (Fondo terrestre y nubes sin negro)
    success_report["stage_01"] = fn01_mcmip_true_color_generate_products(
        file_path, product_out_root, overwrite, indent
    )

    # Stage 02: Colorized IR Clouds (Nubes térmicas sin gris)
    success_report["stage_02"] = fn02_mcmip_colorized_ir_generate_products(
        file_path, product_out_root, overwrite, indent
    )
    
    return success_report

# --- STAGE FUNCTIONS ---

def fn01_mcmip_true_color_generate_products(file_path: Path, product_out_root: Path, overwrite=False, indent=""):
    """
    Stage 01: True Color product generation (Native & WGS84) + Alpha Transparency.
    """
    start_ts = time.time()
    base_name = file_path.stem
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        fn_dir = product_out_root / "fn01"
        fn_dir.mkdir(parents=True, exist_ok=True)

        # Output paths existentes
        out_png_native = fn_dir / f"{base_name}_original_goes.png"
        out_png_wgs84 = fn_dir / f"{base_name}_wgs84.png"
        out_tif_wgs84 = fn_dir / f"{base_name}_wgs84.tif"
        out_json = fn_dir / f"{base_name}_metadata_fn01.json"
        
        # --- NUEVOS PATHS PARA TRANSPARENCIA ---
        out_png_native_trans = fn_dir / f"{base_name}_original_goes_transparent.png"
        out_png_wgs84_trans = fn_dir / f"{base_name}_wgs84_transparent.png"

        # Check overwrite (actualizado con los nuevos archivos)
        if not overwrite and all(p.exists() for p in [out_png_native, out_png_wgs84, out_png_native_trans, out_png_wgs84_trans]):
            print(f"✅ [fn01] Skipping: All products exist.")
            return True

        print(f"⏰ [fn01] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Satpy Cache
        path_cache = satpy_config.get("cache_dir")
        if path_cache: os.environ['PYRESAMPLE_CACHE_DIR'] = str(path_cache)

        # STEP 1: Load Scene
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc')
        scn.load(['true_color'])

        # STEP 2: Save Native Image
        print(f"📸 [fn01] [2/6] Generating native products...")
        scn.save_datasets(writer='simple_image', datasets=['true_color'], 
                          base_dir=str(fn_dir), filename=out_png_native.name)
        
        # GENERAR TRANSPARENCIA NATIVA
        apply_dark_transparency(out_png_native, out_png_native_trans)

        # STEP 3: Grid Definition
        area_def = AreaDefinition(
            'global_wgs84', 'Lat-Lon Global', 'wgs84', 
            {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}, 
            3600, 1800, 
            (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )

        # STEP 4: Resample
        print(f"🔄 [fn01] [4/6] Resampling (kd_tree)...")
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # STEP 5: Export WGS84 products
        print(f"💾 [fn01] [5/6] Exporting WGS84 products...")
        scn_res.save_datasets(writer='simple_image', datasets=['true_color'], 
                              base_dir=str(fn_dir), filename=out_png_wgs84.name)
        
        # GENERAR TRANSPARENCIA WGS84
        apply_dark_transparency(out_png_wgs84, out_png_wgs84_trans)
        
        scn_res.save_datasets(writer='geotiff', datasets=['true_color'], 
                              base_dir=str(fn_dir), filename=out_tif_wgs84.name)

        # STEP 6: Save Audit Metadata
        duration = round((time.time() - start_ts) / 60, 2)
        metadata = {
            "source_file": base_name,
            "version": "v.0.5.1", # Actualizado por tu github
            "stage": "fn01",
            "transparent_generated": True,
            "duration_min": duration,
            "timestamp": datetime.now().isoformat()
        }
        with open(out_json, 'w') as f:
            json.dump(metadata, f, indent=4)

        print(f"✅ [fn01] Finished in {duration} min")
        return True

    except Exception as e:
        print(f"❌ [fn01] CRITICAL ERROR: {str(e)}")
        return False
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr



def fn02_mcmip_colorized_ir_generate_products(file_path: Path, product_out_root: Path, overwrite=False, indent=""):
    """
    Stage 02: Colorized IR Clouds product generation (Native & WGS84) + Grayscale Transparency.
    """
    import time
    import json
    import os
    from datetime import datetime
    from satpy import Scene
    from pyresample import AreaDefinition

    start_ts = time.time()
    base_name = file_path.stem
    
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout = SmartIndentedOutput(original_stdout, indent)
    sys.stderr = SmartIndentedOutput(original_stderr, indent)
    
    try:
        # Carpeta específica para la etapa 02
        fn_dir = product_out_root / "fn02"
        fn_dir.mkdir(parents=True, exist_ok=True)

        # Definición de rutas de salida
        out_png_native = fn_dir / f"{base_name}_ir_original_goes.png"
        out_png_wgs84 = fn_dir / f"{base_name}_ir_wgs84.png"
        out_tif_wgs84 = fn_dir / f"{base_name}_ir_wgs84.tif"
        out_json = fn_dir / f"{base_name}_metadata_fn02.json"
        
        # Paths para transparencia (Quitando grises)
        out_png_native_trans = fn_dir / f"{base_name}_ir_original_goes_transparent.png"
        out_png_wgs84_trans = fn_dir / f"{base_name}_ir_wgs84_transparent.png"

        # Protección de sobreescritura
        if not overwrite and all(p.exists() for p in [out_png_native, out_png_wgs84, out_png_native_trans, out_png_wgs84_trans]):
            print(f"✅ [fn02] Skipping: All products exist in {fn_dir.name}")
            return True

        print(f"⏰ [fn01] Start: {datetime.now().strftime('%H:%M:%S')}")
        
        # Cache de Satpy
        path_cache = satpy_config.get("cache_dir")
        if path_cache: os.environ['PYRESAMPLE_CACHE_DIR'] = str(path_cache)

        # STEP 1: Load Scene
        print(f"📦 [fn02] [1/6] Loading Colorized IR composites...")
        # Usamos h5netcdf para asegurar compatibilidad en la Legion
        scn = Scene(filenames=[str(file_path)], reader='abi_l2_nc', reader_kwargs={'engine': 'h5netcdf'})
        product_id = 'colorized_ir_clouds'
        scn.load([product_id])

        # STEP 2: Save Native Image
        print(f"📸 [fn02] [2/6] Generating native products...")
        scn.save_datasets(writer='simple_image', datasets=[product_id], 
                          base_dir=str(fn_dir), filename=out_png_native.name)
        
        # APLICAR TRANSPARENCIA A GRISES (Aísla las nubes de colores)
        apply_grayscale_transparency(out_png_native, out_png_native_trans)

        # STEP 3: Grid Definition (Idéntica a fn01 para que encajen perfectamente)
        print(f"🗺️  [fn02] [3/6] Defining WGS84 grid...")
        area_def = AreaDefinition(
            'global_wgs84', 'Lat-Lon Global', 'wgs84', 
            {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}, 
            3600, 1800, 
            (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        )

        # STEP 4: Resample
        print(f"🔄 [fn02] [4/6] Resampling (kd_tree)...")
        scn_res = scn.resample(area_def, resampler='kd_tree', cache_dir=path_cache)

        # STEP 5: Export WGS84 products
        print(f"💾 [fn02] [5/6] Exporting WGS84 PNG & GeoTIFF...")
        scn_res.save_datasets(writer='simple_image', datasets=[product_id], 
                              base_dir=str(fn_dir), filename=out_png_wgs84.name)
        
        # TRANSPARENCIA EN WGS84
        apply_grayscale_transparency(out_png_wgs84, out_png_wgs84_trans)
        
        scn_res.save_datasets(writer='geotiff', datasets=[product_id], 
                              base_dir=str(fn_dir), filename=out_tif_wgs84.name)

        # STEP 6: Save Audit Metadata
        duration = round((time.time() - start_ts) / 60, 2)
        metadata = {
            "source_file": base_name,
            "version": "v.0.5.1",
            "stage": "fn02",
            "product_id": "COLORIZED_IR_CLOUDS",
            "grayscale_transparency": True,
            "duration_min": duration,
            "timestamp": datetime.now().isoformat()
        }
        with open(out_json, 'w') as f:
            json.dump(metadata, f, indent=4)

        print(f"✅ [fn02] Finished in {duration} min")
        return True

    except Exception as e:
        print(f"❌ [fn02] CRITICAL ERROR: {str(e)}")
        return False
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
