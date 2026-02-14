import sys
import json
import warnings
import numpy as np
from pathlib import Path
from datetime import datetime
from satpy import Scene
from pyresample.geometry import AreaDefinition

# 1. INTEGRACIÓN CON CONFIGURACIÓN GLOBAL
try:
    from .. import config_satpy
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from goes_processor import config_satpy

warnings.filterwarnings("ignore")

def process_file(input_file, input_base: Path, output_base: Path, format: str = "both", overwrite: bool = False):
    input_file = Path(input_file).resolve()
    input_base = Path(input_base).resolve()
    output_base = Path(output_base).resolve()
    
    # Estructura de salida espejo
    rel_path = input_file.relative_to(input_base)
    final_output_dir = output_base / rel_path.parent / input_file.stem
    final_output_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = input_file.stem
    
    # Definición de las 6 salidas
    png_orig_gray   = final_output_dir / f"{base_name}_original_native_gray.png"
    png_orig_color  = final_output_dir / f"{base_name}_original_native_color.png" # 🌟 Restaurado
    tif_wgs84_gray  = final_output_dir / f"{base_name}_wgs84_gray_data_celsius.tif"
    png_wgs84_gray  = final_output_dir / f"{base_name}_wgs84_gray_preview.png"
    tif_wgs84_color = final_output_dir / f"{base_name}_wgs84_color_enhanced_celsius.tif"
    png_wgs84_color = final_output_dir / f"{base_name}_wgs84_color_preview.png"
    json_meta       = final_output_dir / f"{base_name}_metadata.json"

    try:
        # 2. CARGAR ESCENA
        scn = Scene(filenames=[str(input_file)], reader='abi_l2_nc')
        prod_gray = 'LST'
        prod_color = 'lstf_celsius_color01'
        
        print(f"  - Cargando datasets...")
        scn.load([prod_gray, prod_color])

        # --- 🌟 FIX MANUAL KELVIN A CELSIUS (v.0.0.1) 🌟 ---
        for p in [prod_gray, prod_color]:
            # Verificamos si los datos están en Kelvin (Media > 100)
            if scn[p].mean() > 100:
                print(f"    - [FIX] Restando 273.15 a {p} para obtener Celsius")
                scn[p] = scn[p] - 273.15
                scn[p].attrs['units'] = 'Celsius'
        
        # Verificación rápida para el log
        check_val = scn[prod_gray].values
        clean_val = check_val[~np.isnan(check_val)]
        print(f"    [CHECK] Rango real: {clean_val.min():.2f} a {clean_val.max():.2f} °C")
        # --------------------------------------------------

        # 3. GUARDAR PRODUCTOS ORIGINALES (NATIVOS)
        print(f"  - Guardando PNGs originales (Nativo)...")
        scn.save_dataset(prod_gray, filename=str(png_orig_gray), writer='simple_image')
        scn.save_dataset(prod_color, filename=str(png_orig_color), writer='simple_image')

        # 4. REMUESTREO WGS84 (3600x1800)
        area_def = AreaDefinition(
            'global_wgs84', 'Global WGS84', 'epsg4326', 'EPSG:4326',
            3600, 1800, [-180.0, -90.0, 180.0, 90.0]
        )
        print(f"  - Remuestreando a WGS84...")
        scn_res = scn.resample(area_def)

        # 5. GUARDAR PRODUCTOS WGS84
        print(f"  - Guardando archivos WGS84...")
        # Grises (Datos científicos)
        scn_res.save_dataset(prod_gray, filename=str(tif_wgs84_gray), writer='geotiff', dtype=np.float32)
        scn_res.save_dataset(prod_gray, filename=str(png_wgs84_gray), writer='simple_image')
        # Colores (Visualización)
        scn_res.save_dataset(prod_color, filename=str(tif_wgs84_color), writer='geotiff')
        scn_res.save_dataset(prod_color, filename=str(png_wgs84_color), writer='simple_image')

        # 6. METADATOS
        metadata = {
            "source": input_file.name,
            "units": "Celsius",
            "fixed_kelvin_to_celsius": True,
            "files": {
                "native_color": png_orig_color.name,
                "wgs84_data": tif_wgs84_gray.name,
                "wgs84_color": tif_wgs84_color.name
            }
        }
        with open(json_meta, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)

        return final_output_dir

    except Exception as e:
        print(f"  - [ERROR] {base_name}: {str(e)}")
        raise e
