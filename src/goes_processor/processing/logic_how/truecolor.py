# src/goes19_processor/processing/truecolor.py

from pathlib import Path
from satpy import Scene
from pyresample.geometry import AreaDefinition  # Import necesario para AreaDefinition
import warnings
import json
from datetime import datetime

warnings.filterwarnings("ignore")

def process_file(input_file, input_base: Path, output_base: Path, format: str = "both", overwrite: bool = False):
    # --- 0. NORMALIZACIÓN DE ENTRADA ---
    if isinstance(input_file, list):
        input_file = input_file[0]
       
    input_file = Path(input_file).resolve()
    input_base = Path(input_base).resolve()
    output_base = Path(output_base).resolve()
   
    # 1. ESTRUCTURA DE CARPETAS
    try:
        rel_path = input_file.relative_to(input_base)
        final_output_dir = output_base / rel_path.parent / input_file.stem
    except ValueError:
        final_output_dir = output_base / "external" / input_file.stem
    final_output_dir.mkdir(parents=True, exist_ok=True)
    base_name = input_file.stem

    # Definición de rutas del Pack
    png_original = final_output_dir / f"{base_name}_original_goes.png"
    tif_wgs84 = final_output_dir / f"{base_name}_wgs84.tif"
    png_wgs84 = final_output_dir / f"{base_name}_wgs84.png"
    json_meta = final_output_dir / f"{base_name}_metadata.json"

    try:
        # 2. CARGAR ESCENA
        scn = Scene(filenames=[str(input_file)], reader='abi_l2_nc')
        scn.load(['true_color'])

        # --- A. PNG ORIGINAL (Perspectiva Satelital) ---
        # Guardar con fill_value=None para transparencia fuera del disco
        scn.save_datasets(
            writer='simple_image',
            datasets=['true_color'],
            base_dir=str(final_output_dir),
            filename=f"{base_name}_original_goes.png",
            fill_value=None,          # Fuera del disco → transparente
            compress=True             # Reduce tamaño
        )
        print(f"PNG Nativo guardado: {png_original}")

        # --- B. ENMASCARAMIENTO DE DISCO ---
        # Aplicamos máscara basada en validez (datos reales dentro del disco)
        true_color_masked = scn["true_color"].where(scn["true_color"].notnull())
        scn["true_color_masked"] = true_color_masked

        # 3. DEFINICIÓN DE ÁREA WGS84 (3600 x 1800)
        area_id = 'global_wgs84'
        description = 'Lat-Lon Global Plate Carree'
        proj_id = 'wgs84'
        projection = {'proj': 'eqc', 'lat_ts': 0, 'lat_0': 0, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'WGS84', 'units': 'm'}
        width = 3600
        height = 1800
        area_extent = (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        area_def = AreaDefinition(area_id, description, proj_id, projection, width, height, area_extent)

        # 4. REMUESTREO (Transformación a WGS84)
        print(f"Remuestreando a WGS84 ({width}x{height})...")
        scn_wgs84 = scn.resample(area_def, resampler='bilinear')

        # --- C. GUARDADO EN WGS84 con transparencia ---
        # PNG WGS84 con fill_value=None (transparente fuera del disco)
        scn_wgs84.save_datasets(
            writer='simple_image',
            datasets=['true_color'],
            base_dir=str(final_output_dir),
            filename=f"{base_name}_wgs84.png",
            fill_value=None,          # Transparente fuera del disco
            compress=True
        )

        # TIFF WGS84 con canal alpha (transparencia real en QGIS)
        scn_wgs84.save_datasets(
            writer='geotiff',
            datasets=['true_color'],
            base_dir=str(final_output_dir),
            filename=f"{base_name}_wgs84.tif",
            include_alpha=True,       # Canal alfa para transparencia
            fill_value=0              # Valor de relleno para no-datos
        )

        # --- D. METADATOS JSON ---
        metadata = {
            "archivo_fuente": input_file.name,
            "procesado_el": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "satelite": scn.attrs.get('satellite_name', 'GOES-19'),
            "producto": "MCMIPF - True Color",
            "resolucion_wgs84": "3600x1800 (0.1 deg)",
            "mascara": "Full Disk Masking (Space exclusion applied via fill_value and alpha)",
            "outputs": {
                "png_goes": png_original.name,
                "tif_wgs84": tif_wgs84.name,
                "png_wgs84": png_wgs84.name,
                "json": json_meta.name
            }
        }
        with open(json_meta, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        print("-" * 30)
        print("¡Proceso Exitoso!")
        print(f"1. Nativo: {png_original.name}")
        print(f"2. WGS84 PNG: {png_wgs84.name}")
        print(f"3. WGS84 TIF: {tif_wgs84.name} (Listo para QGIS con transparencia)")
        print(f"4. Metadatos: {json_meta.name}")

        return final_output_dir

    except Exception as e:
        raise RuntimeError(f"Error en True Color v.0.0.1: {str(e)}")
