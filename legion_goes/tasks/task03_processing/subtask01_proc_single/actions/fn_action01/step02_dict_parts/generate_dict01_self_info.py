# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict01_self_info.py
# Version: 1.7.1 (Fixed Imports & Task 03 Logic)
# =============================================================================
from datetime import datetime
from pathlib import Path

# --- IMPORT CORREGIDO ---
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.generate_plan_proc_single_json_file_path import generate_plan_proc_single_json_file_path

def generate_dict(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str) -> dict:
    """Generates metadata about the Processing Plan file itself."""
    time_now = datetime.now()
    time_now_format = time_now.strftime("%Y-%m-%d %H:%M:%S")
  
    # Usamos la utilidad de Task 03 para resolver la ruta del JSON de proceso
    file_path = generate_plan_proc_single_json_file_path(
        sat_id=sat_id,
        product_id=product_id,
        year=year,
        day=day,
        fnp_tag=fnp_tag
    )
      
    return {
        "description": f"Processing Single Plan for 1 day, product {product_id}, tag {fnp_tag}.",
        "version_github": "v.0.0.1",
        "file_name": file_path.name,
        "path_absolute": str(file_path.resolve()),
        "created_at_local": time_now_format
    }

# ===================================================================
# MAIN EXECUTION
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE PROCESSING PLAN METADATA ".center(80, "="))

    # 1. Configuración de prueba
    params = {
        "sat_id": "19",
        "product_id": "ABI-L2-MCMIPF",
        "year": "2026",
        "day": "003",
        "fnp_tag": "fnp01"
    }

    try:
        # 2. Generar el diccionario de información propia
        metadata = generate_dict(**params)
        
        # 3. Print elegante
        print(f"🛰️  Satellite : GOES-{params['sat_id']}")
        print(f"📦 Product   : {params['product_id']}")
        print(f"📅 Date      : {params['year']}-{params['day'].zfill(3)}")
        print(f"🏷️  Tag       : {params['fnp_tag']}")
        print("-" * 80)
        
        print("📝 Metadata generated:")
        for key, value in metadata.items():
            print(f"   ➤ {key:<16}: {value}")
            
        print("\n" + "✅ TEST COMPLETED".center(80, " "))
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

    print("=" * 80 + "\n")
