# =============================================================================
# Path: legion_goes/code/python_sp/f02_processing/sp001_single/f02_auto_processing/run_executor.py
# Version: 1.2.6 (Fix: Sequential argument logic for Timestamp Util)
# =============================================================================

import time
from pathlib import Path
from typing import List, Dict, Any

# --- ABSOLUTE IMPORTS ---
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn01_run_collector.run_collector import run_collector
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.get_str_s_timestamp_short_from_nc import get_str_s_timestamp_short_from_nc

def run_executor(nc_path: str, fnp_tag: str = "fnp01") -> bool:
    """
    Motor de ejecución autónomo.
    Extrae Product ID primero para poder obtener el Timestamp correcto según SOT.
    """
    path_obj = Path(nc_path)
    if not path_obj.exists():
        print(f"❌ [EXECUTOR] No existe el archivo: {nc_path}")
        return False

    try:
        # --- 1. EXTRACCIÓN PRIMARIA (Nombre del archivo) ---
        str_file_name = path_obj.name
        parts = str_file_name.split('_')
        
        # El Product ID suele ser la segunda parte: OR_ABI-L2-LSTF-M6...
        # Lo limpiamos del sufijo de modo (-M6, -M4, etc) si es necesario
        raw_product = parts[1]
        product_id = raw_product.split('-M')[0] if '-M' in raw_product else raw_product
        
        # Satélite (G16, G17, G19...) -> Limpiamos a '16', '17', '19'
        sat_id = parts[2].replace("G", "")

        # --- 2. EXTRACCIÓN DE TIMESTAMP (Usando la util corregida) ---
        # Ahora pasamos el product_id que extrajimos arriba
        s_timestamp_short = get_str_s_timestamp_short_from_nc(
            product_id=product_id, 
            input_nc=str_file_name
        )
        
        if not s_timestamp_short:
            print(f"❌ [EXECUTOR] No se pudo extraer timestamp de {str_file_name}")
            return False

        # Año y Día desde el s_timestamp_short (formato sYYYYDDD...)
        year = int(s_timestamp_short[1:5])
        day = int(s_timestamp_short[5:8])
        
    except Exception as e:
        print(f"❌ [EXECUTOR] Error en la fase de metadatos: {e}")
        return False

    # --- 3. LLAMADA AL COLLECTOR ---
    execution_plan = run_collector(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day, 
        s_timestamp_short=s_timestamp_short, 
        fnp_tag=fnp_tag
    )

    if not execution_plan or len(execution_plan) < 3:
        print(f"❌ [EXECUTOR] Collector no pudo generar el plan para {s_timestamp_short}")
        return False

    # --- 4. PIPELINE SECUENCIAL ---
    pipeline_start = time.time()
    print("\n" + f" 🚀 PROCESANDO: {str_file_name} ".center(80, "="))
    
    try:
        # PACK 01: CIENCIA
        bag01 = execution_plan[0]
        print(f"\n▶️  [1/3] {bag01['meta']['task_name']}")
        res01 = bag01['fnp_python_code'](nc_path=nc_path, **bag01['execution_kwargs'])
        if not res01: return False

        # PACK 02: GALERÍA
        bag02 = execution_plan[1]
        print(f"\n▶️  [2/3] {bag02['meta']['task_name']}")
        res02 = bag02['fnp_python_code'](**bag02['execution_kwargs'])

        # PACK 03: METADATA
        bag03 = execution_plan[2]
        print(f"\n▶️  [3/3] {bag03['meta']['task_name']}")
        res03 = bag03['fnp_python_code'](start_time=pipeline_start, **bag03['execution_kwargs'])

        total_time = round(time.time() - pipeline_start, 2)
        print("\n" + f" ✅ ÉXITO EN {total_time}s ".center(80, "=") + "\n")
        return True

    except Exception as e:
        print(f"\n💥 [EXECUTOR ERROR] {e}")
        return False

# =============================================================================
# MAIN: TEST LOCAL
# =============================================================================
if __name__ == "__main__":
    base_dir = Path(".")
    nc_files = sorted(list(base_dir.glob("*.nc")))
    
    if nc_files:
        test_file = str(nc_files[0].absolute())
        print(f"🎯 Iniciando Executor con: {nc_files[0].name}")
        run_executor(nc_path=test_file, fnp_tag="fnp01")
    else:
        print(f"⚠️ No se encontraron archivos .nc en {base_dir.absolute()}")
