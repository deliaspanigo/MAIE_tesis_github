# =============================================================================
# FILE PATH: src/goes_processor/SoT/goes_sat.py
# Version: 0.1.8 (Fixed Syntax & True Julian/Gregorian separation)
# =============================================================================

try:
    from types import MappingProxyType
    from datetime import datetime
    import re
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SoT - goes_sat.py]")
    print("="*80)
    print(f" Failed to load base libraries: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print(" Ensure that all required libraries are correctly installed.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# GEOGRAPHIC POSITIONS (Single Source of Truth)
# ===================================================================
AVAILABLE_GOES_SAT_POSITIONS = ("east", "west")
AVAILABLE_GOES_SAT_POSITIONS_WITH_ALL = AVAILABLE_GOES_SAT_POSITIONS + ("ALL",)

# ===================================================================
# REQUIRED FIELDS
# ===================================================================
REQUIRED_FIELDS = frozenset({
    "bucket",
    "name01", "name02", "name03", "name04", "name05", "name06",
    "default_position",
    "status",
    "first_date_julian", "last_date_julian",
    "first_date_gregorian", "last_date_gregorian"
})

# ===================================================================
# PRIVATE SOURCE OF TRUTH
# ===================================================================
_PRIVATE_SAT_INFO = {
    "meta": {
        "version": "0.1.8",
        "series": "GOES-R",
        "description": "Master Config - NOAA GOES Identity and Transitions",
        "transitions_gregorian": {
            "east_16_to_19": datetime(2025, 4, 1),
            "west_17_to_18": datetime(2023, 1, 4)
        },
        "transitions_julian": {
            "east_16_to_19": datetime(2025, 4, 1), # Se evalúa como objeto datetime
            "west_17_to_18": datetime(2023, 1, 4)
        }
    },
    "16": {
        "bucket": "noaa-goes16",
        "name01": "16", "name02": "g16", "name03": "goes16",
        "name04": "goes-east", "name05": "goes16-east", "name06": "GOES16",
        "default_position": "east",
        "status": "standby",
        "first_date_julian": "2016-353", "last_date_julian": None,
        "first_date_gregorian": "2016-12-18", "last_date_gregorian": None
    },
    "17": {
        "bucket": "noaa-goes17",
        "name01": "17", "name02": "g17", "name03": "goes17",
        "name04": "goes-west", "name05": "goes17-west", "name06": "GOES17",
        "default_position": "west",
        "status": "standby",
        "first_date_julian": "2018-043", "last_date_julian": None,
        "first_date_gregorian": "2018-02-12", "last_date_gregorian": None
    },
    "18": {
        "bucket": "noaa-goes18",
        "name01": "18", "name02": "g18", "name03": "goes18",
        "name04": "goes-west", "name05": "goes18-west", "name06": "GOES18",
        "default_position": "west",
        "status": "active",
        "first_date_julian": "2022-060", "last_date_julian": None,
        "first_date_gregorian": "2022-03-01", "last_date_gregorian": None
    },
    "19": {
        "bucket": "noaa-goes19",
        "name01": "19", "name02": "g19", "name03": "goes19",
        "name04": "goes-east", "name05": "goes19-east", "name06": "GOES19",
        "default_position": "east",
        "status": "active",
        "first_date_julian": "2024-177", "last_date_julian": None,
        "first_date_gregorian": "2024-06-25", "last_date_gregorian": None
    }
}

SAVED_INFO_SAT_GOES = MappingProxyType({
    k: MappingProxyType(v) if isinstance(v, dict) else v
    for k, v in _PRIVATE_SAT_INFO.items()
})

# ===================================================================
# INTERNAL VALIDATORS
# ===================================================================
def _validate_inputs(year=None, day_julian=None, sat_id=None, sat_position=None):
    # Define file context for the error message
    ctx = "[SoT - goes_sat.py -  _validate_inputs()]"
    
    try:
        # 1. Year Validation
        if year is not None and not re.match(r'^\d{4}$', str(year)):
            raise ValueError(f"Invalid year '{year}': must be YYYY.")
        
        # 2. Julian Day Validation
        if day_julian is not None:
            if not re.match(r'^\d{3}$', str(day_julian)) or not (1 <= int(day_julian) <= 366):
                raise ValueError(f"Invalid Julian day '{day_julian}': must be DDD (001-366).")
                
        # 3. Position Validation (Strict)
        if sat_position is not None:
            if sat_position not in AVAILABLE_GOES_SAT_POSITIONS:
                raise ValueError(f"Invalid position '{sat_position}'. Must be lowercase. Use: {AVAILABLE_GOES_SAT_POSITIONS}")
                
        # 4. Sat ID Validation
        if sat_id is not None:
            valid_ids = [k for k in SAVED_INFO_SAT_GOES.keys() if k != "meta"]
            if str(sat_id) not in valid_ids:
                raise ValueError(f"Sat ID '{sat_id}' not found. Valid IDs: {valid_ids}")

    except ValueError as e:
        # Wraps the specific error with the file context
        raise ValueError(f"\n[CRITICAL]{ctx}:  {e}") from None

# ===================================================================
# PUBLIC ACCESS METHODS
# ===================================================================

def get_goes_id_by_julian_date(year: str, day: str, sat_position: str = "east") -> str:
    """Finds active satellite using YYYY and DDD."""
    ctx = "[SoT - goes_sat.py - get_goes_id_by_julian_date()]"
    
    try:
        # 1. Run the internal validation
        _validate_inputs(year=year, day_julian=day, sat_position=sat_position)
        
        # 2. Date object creation (Julian format)
        try:
            date_obj = datetime.strptime(f"{year}-{day}", "%Y-%j")
        except ValueError as e:
            raise ValueError(f"Invalid Julian Date format: {e}")

        # 3. Logic to determine the satellite
        try:
            trans = SAVED_INFO_SAT_GOES["meta"]["transitions_julian"]
            
            if sat_position == "east":
                return "16" if date_obj < trans["east_16_to_19"] else "19"
            
            return "17" if date_obj < trans["west_17_to_18"] else "18"
        except KeyError as e:
            raise KeyError(f"Internal Dictionary Error - Missing transition key: {e}")

    except (ValueError, KeyError) as e:
        # Unificamos la salida para mantener el estándar visual
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None


def get_goes_id_by_gregorian_date(year: str, month: str, day: str, sat_position: str = "east") -> str:
    """Finds active satellite using YYYY, MM, and DD."""
    ctx = "[SoT - goes_sat.py - get_goes_id_by_gregorian_date()]"
    
    try:
        # 1. Run internal validation
        _validate_inputs(year=year, sat_position=sat_position)
        
        # 2. Date object creation
        try:
            date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid Date format/values: {e}")

        # 3. Logic to determine the satellite
        # Capturamos posibles fallos de llaves en el diccionario meta
        try:
            trans = SAVED_INFO_SAT_GOES["meta"]["transitions_gregorian"]
            
            if sat_position == "east":
                return "16" if date_obj < trans["east_16_to_19"] else "19"
            
            return "17" if date_obj < trans["west_17_to_18"] else "18"
        except KeyError as e:
            raise KeyError(f"Internal Dictionary Error - Missing transition key: {e}")

    except (ValueError, KeyError) as e:
        # Ahora ambos tipos de error salen con este formato profesional
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None



def get_satellite_info(sat_id: str) -> MappingProxyType:
    """Returns the full dictionary for a specific satellite ID."""
    ctx = "[SoT - goes_sat.py - get_satellite_info()]"
    
    try:
        # 1. Validate if the ID exists in our allowed list
        _validate_inputs(sat_id=sat_id)
        
        # 2. Attempt to retrieve the data
        try:
            return SAVED_INFO_SAT_GOES[str(sat_id)]
        except KeyError:
            raise KeyError(f"Data for Satellite ID '{sat_id}' is missing from the Source of Truth dictionary.")

    except (ValueError, KeyError) as e:
        # Unified error format for v.0.1.8
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None
        
        

def get_goes_bucket(sat_id: str) -> str:
    """Returns the S3 bucket name for a specific satellite ID."""
    ctx = "[SoT - goes_sat.py - get_goes_bucket()]"
    
    try:
        # 1. Obtenemos el diccionario del satélite (ya validado por get_satellite_info)
        info = get_satellite_info(sat_id)
        
        # 2. Extraemos el bucket con validación de existencia de la llave
        if "bucket" not in info:
            raise KeyError(f"Key 'bucket' is missing for Satellite ID '{sat_id}'.")
            
        return info["bucket"]

    except (ValueError, KeyError) as e:
        # Unificamos el error con el formato de cascada
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}") from None

# ===================================================================
# INTEGRITY CHECK
# ===================================================================
def _validate_module_integrity():
    """Checks internal dictionary consistency, required fields, and date formats."""
    ctx = "[SoT - goes_sat.py - _validate_module_integrity()]"
    
    # Regex pre-compilados para performance
    julian_regex = re.compile(r'^\d{4}-\d{3}$')
    gregorian_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    for sat_id, data in _PRIVATE_SAT_INFO.items():
        if sat_id == "meta":
            continue
        
        # 1. Verificar campos obligatorios
        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ImportError(f"\n{ctx} Satellite '{sat_id}' is missing required keys: {missing}\n")
        
        # 2. Validar formatos de fecha (Solo si no son None)
        # Usamos un pequeño mapeo para no repetir código de validación
        date_checks = {
            "first_date_julian": julian_regex,
            "first_date_gregorian": gregorian_regex
        }

        for field, regex in date_checks.items():
            val = data.get(field)
            if val is None:
                raise ImportError(f"\n{ctx} Sat {sat_id}: '{field}' cannot be None. Critical for timeline mapping.\n")
            
            if not regex.match(str(val)):
                expected = "YYYY-DDD" if "julian" in field else "YYYY-MM-DD"
                raise ImportError(
                    f"\n{ctx} Format Mismatch!\n"
                    f"    Satellite: {sat_id}\n"
                    f"    Field:     {field}\n"
                    f"    Value:     '{val}'\n"
                    f"    Expected:  {expected}\n"
                )

# Execute integrity check on import
_validate_module_integrity()
