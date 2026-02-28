# =============================================================================
# FILE PATH: src/goes_processor/info/goes_prod.py
# Version: 0.1.8 (Strict Library & Integrity Validation)
# =============================================================================

try:
    from types import MappingProxyType
    import re
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [info - goes_prod.py]")
    print("="*80)
    print(f" Failed to load base libraries: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# REQUIRED KEYS
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
        "full_name": "Land Surface Temperature (Full Disk)",
        "description": "Land Surface Temperature product",
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
    # ... (Tus otros productos ABI-L2-MCMIPF, ABI-L2-FDCF, GLM-L2-LCFA)
}

# ===================================================================
# INTERNAL INTEGRITY CHECK
# ===================================================================
def _validate_module_integrity():
    """Checks internal product dictionary consistency and required fields."""
    ctx = "[CRITICAL - goes_prod.py - _validate_module_integrity]"
    
    for prod_id, data in _PRIVATE_PRODUCTS.items():
        # 1. Common keys
        missing_common = REQUIRED_KEYS - data.keys()
        if missing_common:
            raise ImportError(f"\n{ctx} Product '{prod_id}' is missing common keys: {missing_common}\n")

        # 2. Type-specific
        p_type = data.get("type")
        if p_type == "raster":
            missing = REQUIRED_RASTER_KEYS - data.keys()
        elif p_type == "vectorial":
            missing = REQUIRED_VECTORIAL_KEYS - data.keys()
        else:
            raise ImportError(f"\n{ctx} Product '{prod_id}' has invalid type: '{p_type}'.\n")

        if missing:
            raise ImportError(f"\n{ctx} Type '{p_type}' Mismatch in '{prod_id}'. Missing: {missing}\n")

# Ejecución automática al importar
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
