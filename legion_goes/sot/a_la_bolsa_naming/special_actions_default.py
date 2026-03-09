"""
Path: src/legion_goes/SoT/special_actions_default.py
Version: 0.3.0
Description: Detalle de todas las accioens y subacciones (core) para el procesador.
"""

# ... (Imports de goes_sat y goes_prod se mantienen iguales) ...



the_actions = {
    "planning": {
    "pos": "00",
    "init_plan_file_name": None,
    },
    "download": {
        "pos": "01",
        "init_plan_file_name": "plan_01_downlaod",
        },
    "processing":{
        "pos": "02",
        "init_plan_file_name": "plan_02_processing",},
        "list_core": {
            "core01": 
                "folder_name": "core01_sp_single",
            "core02":}
}

def _get_sat_position_from_sot(sat_id: str) -> str:
    """
    Internal helper to fetch the official position from goes_sat.py.
    """
    clean_id = str(sat_id).upper().replace("GOES-", "").replace("GOES", "").replace("G", "").strip()
    
    if clean_id not in SAVED_INFO_SAT_GOES:
        raise ValueError(f"Satellite ID '{sat_id}' not found in SoT.")
    
    # Obtenemos la posición (east/west) directamente del SoT de satélites
    return SAVED_INFO_SAT_GOES[clean_id]["position"].upper()

def generate_name_part01(level_key: str, sat_id: str) -> str:
    """
    Generates: SP-LEVEL_GOESXX-POSITION
    Position is now INFERRED from the Satellite ID.
    """
    ctx = "[SoT - naming_conventions.py - generate_name_part01()]"
    try:
        l_key = str(level_key).lower()
        lvl = PRODUCT_LEVELS[l_key] # Valida nivel
        
        # Inferencia de posición
        pos = _get_sat_position_from_sot(sat_id)
        
        # Limpieza de ID para el nombre
        clean_id = str(sat_id).upper().replace("GOES-", "").replace("GOES", "").replace("G", "").strip()
        
        return f"{lvl['prefix']}-{lvl['code_short']}_GOES{clean_id}-{pos}"
    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n")

def generate_name_part03(sat_id, fn_code=None, crs_mode="WGS84", suffix="COLOR", ext="png") -> str:
    """
    Generates the final block.
    If crs_mode is 'NATIVE', it automatically converts to 'GOES-POSITION'.
    """
    ctx = "[SoT - naming_conventions.py - generate_name_part03()]"
    parts = []
    try:
        if fn_code:
            parts.append(str(fn_code).upper())

        # Lógica de CRS Inteligente
        mode = str(crs_mode).upper().strip()
        pos = _get_sat_position_from_sot(sat_id) # 'EAST' o 'WEST'

        if mode == "NATIVE":
            parts.append(f"CRS-GOES-{pos}")
        elif mode == "WGS84":
            parts.append("CRS-WGS84")
        else:
            # Si el usuario pone algo manual, validamos que no mienta
            # Ej: Si pone GOES-WEST pero el sat es el 16 (EAST), lanzamos error.
            if "GOES" in mode and pos not in mode:
                raise ValueError(f"CRS mismatch. Sat {sat_id} is {pos}, but CRS requested is {mode}.")
            parts.append(f"CRS-{mode}")

        parts.append(str(suffix).upper())
        
        clean_ext = str(ext).lower().replace(".", "").strip()
        return f"{'_'.join(parts)}.{clean_ext}"
    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n")

# ===================================================================
# MASTER FUNCTION (Simplified Interface)
# ===================================================================

def get_full_filename(level, sat, prod, time, fn=None, crs="WGS84", suffix="COLOR", ext="png"):
    """
    Simplified entry point. No longer requires 'pos' argument.
    """
    p1 = generate_name_part01(level, sat)
    p2 = generate_name_part02(prod, time)
    p3 = generate_name_part03(sat, fn, crs, suffix, ext)
    
    return f"{p1}_{p2}_{p3}"
