# =============================================================================
# FILE PATH: src/goes_processor/SoT/goes_prod.py
# Version: 1.0.1 (Strict Library & Integrity Validation)
# =============================================================================

try:
    from types import MappingProxyType
    import re
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SoT - goes_prod.py]")
    print("="*80)
    print(f" Failed to load base libraries: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# REQUIRED KEYS (Mandatory for all products)
# ===================================================================
REQUIRED_KEYS = frozenset({
    "full_name", "description", "level", "init_file_name",
    "units", "typical_range", "main_use", "notes",
    "total_files_one_day", "time_lapse", "time_lapse_label",
    "type", "default_time"
})

REQUIRED_RASTER_KEYS = frozenset({
    "cadence_full_disk", "resolution_nominal", "shape_full_disk"
})

REQUIRED_VECTORIAL_KEYS = frozenset({
    "cadence", "cadence_grouped", "resolution_spatial", "shape"
})

# ===================================================================
# PRIVATE SOURCE OF TRUTH
# ===================================================================
_PRIVATE_PRODUCTS = {
    "ABI-L2-LSTF": {
        "full_name": "Land Surface Temperature",
        "description": "Land Surface Temperature product (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-LSTF-M6_G",
        "units": "Kelvin (original) → Celsius (post-processed)",
        "typical_range": "-100 °C to +100 °C",
        "main_use": "Drought monitoring, vegetation thermal stress",
        "notes": "Values outside disk = fill (NaN).",
        "total_files_one_day": 24,
        "time_lapse": "01hour",
        "time_lapse_label": "time_lapse_01hour",
        "type": "raster",
        "cadence_full_disk": "1 hour",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": None,
            "seconds": None
        }
    },
    "ABI-L2-MCMIPF": {
        "full_name": "Cloud and Moisture Imagery",
        "description": "Multiband imagery product (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-MCMIPF-M6_G",
        "units": "Reflectance/Brightness Temp",
        "typical_range": "0-100% / 0-400K",
        "main_use": "General forecasting and imagery",
        "notes": "Full Disk, contains all ABI bands",
        "total_files_one_day": 144,
        "time_lapse": "01hour",
        "time_lapse_label": "time_lapse_01hour",
        "type": "raster",
        "cadence_full_disk": "1 hour",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)], 
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)], 
            "seconds": None
        }
    },
    "ABI-L2-FDCF": {
        "full_name": "Fire Detection and Characterization",
        "description": "Fire hot spot detection and characterization (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-FDCF-M6_G",
        "units": "Kelvin (Fire Temperature), Megawatts (Fire Power)",
        "typical_range": "300K - 1200K",
        "main_use": "Wildfire detection and monitoring",
        "notes": "Includes Fire Temperature, Area, and Power (FRP).",
        "total_files_one_day": 144,
        "time_lapse": "01hour",
        "time_lapse_label": "time_lapse_01hour",
        "type": "raster",
        "cadence_full_disk": "1 hour",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)], 
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)], 
            "seconds": None
        }
    },
    "GLM-L2-LCFA": {
        "full_name": "Lightning Detection",
        "description": "Geostationary Lightning Mapper events",
        "level": "L2",
        "init_file_name": "OR_GLM-L2-LCFA_G",
        "units": "Events/Flashes",
        "typical_range": "N/A",
        "main_use": "Storm intensification monitoring",
        "notes": "Vectorial data",
        "total_files_one_day": 4320, 
        "time_lapse": "20sec",
        "time_lapse_label": "time_lapse_20sec",
        "type": "vectorial",
        "cadence": "20 seconds",
        "cadence_grouped": "1 min",
        "resolution_spatial": "8 km",
        "shape": None,
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)], 
            "minutes": [f"{m:02d}" for m in range(0, 60,  1)], 
            "seconds": [f"{m:02d}" for m in range(0, 60, 20)], 
        }
    }
}

# ===================================================================
# INTERNAL INTEGRITY CHECK
# ===================================================================
def _validate_module_integrity():
    """Checks internal product dictionary consistency and required fields."""
    ctx = "[CRITICAL - goes_prod.py - _validate_module_integrity]"
    
    for prod_id, data in _PRIVATE_PRODUCTS.items():
        # 1. Check Common keys
        missing_common = REQUIRED_KEYS - data.keys()
        if missing_common:
            raise ImportError(f"\n{ctx} Product '{prod_id}' is missing common keys: {missing_common}\n")

        # 2. Check Type-specific keys
        p_type = data.get("type")
        if p_type == "raster":
            missing = REQUIRED_RASTER_KEYS - data.keys()
        elif p_type == "vectorial":
            missing = REQUIRED_VECTORIAL_KEYS - data.keys()
        else:
            raise ImportError(f"\n{ctx} Product '{prod_id}' has invalid type: '{p_type}'.\n")

        if missing:
            raise ImportError(f"\n{ctx} Type '{p_type}' Mismatch in '{prod_id}'. Missing: {missing}\n")

# Automatic execution upon import
_validate_module_integrity()

# ===================================================================
# PUBLIC INTERFACE
# ===================================================================
SAVED_INFO_PROD_GOES = MappingProxyType({
    k: MappingProxyType(v) if isinstance(v, dict) else v
    for k, v in _PRIVATE_PRODUCTS.items()
})

AVAILABLE_GOES_PRODUCTS = tuple(SAVED_INFO_PROD_GOES.keys())

def get_product_info(prod_id: str) -> MappingProxyType:
    """Returns the full metadata dictionary for a specific GOES product."""
    ctx = "[CRITICAL - goes_prod.py - get_product_info()]"
    try:
        if prod_id not in SAVED_INFO_PROD_GOES:
            raise KeyError(f"Product ID '{prod_id}' not found. Available: {AVAILABLE_GOES_PRODUCTS}")
        return SAVED_INFO_PROD_GOES[prod_id]
    except (KeyError, ValueError) as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None
