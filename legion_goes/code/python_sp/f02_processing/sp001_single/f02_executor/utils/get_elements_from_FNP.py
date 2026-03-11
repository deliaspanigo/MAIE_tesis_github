"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/get_elements_from_fnp.py
Version: 0.0.1
Description: Dynamic module loader for FNP processing logic.
"""

import sys
import importlib

def get_elements_from_FNP(product_id, fnp_tag, list_expected):
    """
    Dynamically imports the processing module based on product and tag.
    
    Args:
        product_id (str): GOES Product ID (e.g., 'ABI-L2-MCMIPF').
        fnp_tag (str): Processing tag (e.g., 'fnp01').
        list_expected (list): Attributes to extract from the module (e.g., ['fnp_python_code']).
        
    RETURNS:
        dict: A 'BAG' with the requested elements, or None if import fails.
    """
    # Normalizamos el product_id para que coincida con el nombre de la carpeta (guiones bajos)
    prod_id_mod = product_id.upper().replace('-', '_')
    
    # Construimos el path absoluto de importación
    module_path = f"legion_goes.code.python_sp.sp001_single.f01_product_proc.{prod_id_mod}.{fnp_tag}.fn01_python_code"

    try:
        # Si el módulo ya fue cargado previamente, lo recargamos para asegurar frescura (útil en loops largos)
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        
        # Importación dinámica
        fnp_mod = importlib.import_module(module_path)
        
        # Construimos el BAG (diccionario de resultados)
        # getattr busca la variable dentro del módulo; si no existe, devuelve None.
        bag = {elem: getattr(fnp_mod, elem, None) for elem in list_expected}
        
        return bag

    except Exception as e:
        print(f"      ❌ [STEP02 ERROR] Could not load {module_path}: {e}")
        return None

# =============================================================================
# MAIN (Diagnostic Test)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: STEP02 DYNAMIC IMPORT ".center(60, "="))
    
    # Simulación de carga para MCMIPF
    # Nota: Este test solo funcionará si la estructura de carpetas y el archivo fn01_python_code existen.
    test_list = ['dict_output_schema', 'fnp_python_code']
    
    print(f"Attempting to load MCMIPF fnp01...")
    bag_test = get_elements_from_FNP(
        product_id="ABI-L2-MCMIPF", 
        fnp_tag="fnp01", 
        list_expected=test_list
    )
    
    if bag_test:
        print("✅ Module loaded successfully!")
        for key, value in bag_test.items():
            print(f"   - Found {key}: {type(value)}")
    else:
        print("❌ Test failed. Check if the module path exists and is a valid python package.")
    
    print("=" * 60 + "\n")
