# =============================================================================
# FILE PATH: src/legion_goes/sot/goes_info_product.py
# Version: 1.0.5 (Strict Guarding & Self-Aware Error Context)
# =============================================================================
try:
    from types import MappingProxyType
    import sys
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SOT - goes_info_product.py]")
    print("="*80)
    print(f" Failed to load base libraries: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# REQUIRED KEYS (Mandatory for all products)
# ===================================================================
REQUIRED_KEYS = frozenset({
    "id", "full_name", "description", "level", "init_file_name",
    "units", "typical_range", "main_use", "notes",
    "total_files_one_day", "time_lapse", "time_lapse_label",
    "type", "default_time"
})
REQUIRED_RASTER_KEYS = frozenset({
    "cadence_full_disk", "resolution_nominal", "shape_full_disk"
})
REQUIRED_VECTORIAL_KEYS = frozenset({
    "cadence_full_disk", "cadence_grouped", "resolution_spatial", "shape"
})

# ===================================================================
# PRIVATE SOURCE OF TRUTH
# ===================================================================
_PRIVATE_PRODUCTS = {
    "ABI-L2-LSTF": {
        "id": "ABI-L2-LSTF",
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
            "minutes": [""],
            "seconds": [""]
        }
    },
    "ABI-L2-MCMIPF": {
        "id": "ABI-L2-MCMIPF",
        "full_name": "Cloud and Moisture Imagery",
        "description": "Multiband imagery product (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-MCMIPF-M6_G",
        "units": "Reflectance/Brightness Temp",
        "typical_range": "0-100% / 0-400K",
        "main_use": "General forecasting and imagery",
        "notes": "Full Disk, contains all ABI bands",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)],
            "seconds": [""]
        }
    },
    "ABI-L2-FDCF": {
        "id": "ABI-L2-FDCF",
        "full_name": "Fire Detection and Characterization",
        "description": "Fire hot spot detection and characterization (Full Disk)",
        "level": "L2",
        "init_file_name": "OR_ABI-L2-FDCF-M6_G",
        "units": "Kelvin (Fire Temp), Megawatts (Fire Power)",
        "typical_range": "300K - 1200K",
        "main_use": "Wildfire detection and monitoring",
        "notes": "Includes Fire Temperature, Area, and Power (FRP).",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424),
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 10)],
            "seconds": [""]
        }
    },
    "GLM-L2-LCFA": {
        "id": "GLM-L2-LCFA",
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
        "cadence_full_disk": "20 seconds",
        "cadence_grouped": "1 min",
        "resolution_spatial": "8 km",
        "shape": None,
        "default_time": {
            "hours": [f"{m:02d}" for m in range(0, 24, 1)],
            "minutes": [f"{m:02d}" for m in range(0, 60, 1)],
            "seconds": [f"{m:02d}" for m in range(0, 60, 20)],
        }
    }
}

# ===================================================================
# INTERNAL INTEGRITY CHECK
# ===================================================================
def _validate_module_integrity():
    """Checks internal product dictionary consistency and required fields."""
    ctx = "[CRITICAL - goes_info_product.py - _validate_module_integrity]"

    for product_id, data in _PRIVATE_PRODUCTS.items():
        missing_common = REQUIRED_KEYS - data.keys()
        if missing_common:
            raise ImportError(f"\n{ctx} Product '{product_id}' is missing common keys: {missing_common}")

        p_type = data.get("type")
        if p_type == "raster":
            missing = REQUIRED_RASTER_KEYS - data.keys()
        elif p_type == "vectorial":
            missing = REQUIRED_VECTORIAL_KEYS - data.keys()
        else:
            raise ImportError(f"\n{ctx} Product '{product_id}' has invalid type: '{p_type}'.")

        if missing:
            raise ImportError(f"\n{ctx} Type '{p_type}' mismatch in '{product_id}'. Missing: {missing}")

_validate_module_integrity()

# ===================================================================
# IMMUTABLE EXPORT (Deep Protection)
# ===================================================================
def _make_deep_immutable(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: _make_deep_immutable(v) for k, v in obj.items()})
    elif isinstance(obj, (list, tuple)):
        return tuple(_make_deep_immutable(i) for i in obj)
    return obj

SAVED_INFO_PROD_GOES = _make_deep_immutable(_PRIVATE_PRODUCTS)
AVAILABLE_GOES_PRODUCTS = tuple(SAVED_INFO_PROD_GOES.keys())

# ===================================================================
# CONTROL FUNCTIONS (The Guards)
# ===================================================================
def control_product_id(product_id: str):
    """
    GUARD: Validates the product_id against the SoT.
    Does NOT return anything. Raises an error if validation fails.
    """
    ctx = sys._getframe().f_code.co_name

    if product_id is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' is None. A valid product_id is required.")

    if not isinstance(product_id, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' must be a string, not {type(product_id).__name__}.")

    if " " in product_id:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'product_id' '{product_id}' contains spaces. Provide a clean string.")

    if product_id not in AVAILABLE_GOES_PRODUCTS:
        options = ", ".join(AVAILABLE_GOES_PRODUCTS)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Product '{product_id}' not registered.\nAllowed IDs: {options}")

# ===================================================================
# PUBLIC INTERFACE
# ===================================================================
def get_SOT_goes_info_product(product_id: str = None) -> MappingProxyType:
    """
    Returns specific product metadata or the full catalog from the Source of Truth (SoT).
    Extremely strict access with validation.
    """
    if product_id is None:
        return SAVED_INFO_PROD_GOES

    try:
        control_product_id(product_id)
        return SAVED_INFO_PROD_GOES[product_id]
    except Exception as e:
        ctx = sys._getframe().f_code.co_name
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Failed to resolve product '{product_id}'. Details: {e}"
        raise type(e)(error_msg) from None

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: PRODUCT SOT UNIT TESTS ".center(80, "="))
    print("Running strict integrity and logic tests...\n")

    try:
        # Test 1: Full catalog retrieval
        catalog = get_SOT_goes_info_product()
        assert isinstance(catalog, MappingProxyType), "Catalog must be immutable proxy"
        assert len(catalog) == 4, f"Expected 4 products, got {len(catalog)}"
        print("✅ Test 1: Full catalog retrieval → OK (4 products, immutable)")

        # Test 2: Specific product metadata
        lstf_info = get_SOT_goes_info_product("ABI-L2-LSTF")
        assert lstf_info["type"] == "raster", "ABI-L2-LSTF type mismatch"
        assert lstf_info["cadence_full_disk"] == "1 hour", "ABI-L2-LSTF cadence mismatch"
        print("✅ Test 2: Specific product 'ABI-L2-LSTF' → OK")

        # Test 3: Vectorial product check
        glm_info = get_SOT_goes_info_product("GLM-L2-LCFA")
        assert glm_info["type"] == "vectorial", "GLM-L2-LCFA type mismatch"
        assert glm_info["total_files_one_day"] == 4320, "GLM-L2-LCFA files per day mismatch"
        print("✅ Test 3: Vectorial product 'GLM-L2-LCFA' → OK")

        # Test 4: Invalid product ID (should raise)
        try:
            get_SOT_goes_info_product("INVALID-PROD")
            print("❌ Test 4: Invalid ID should raise → FAILED (no raise)")
        except ValueError:
            print("✅ Test 4: Invalid product ID correctly raises error")

        # Test 5: Invalid type input (should raise)
        try:
            get_SOT_goes_info_product(123)
            print("❌ Test 5: Invalid type should raise → FAILED (no raise)")
        except TypeError:
            print("✅ Test 5: Invalid input type correctly raises error")

        print("\n" + " ALL TESTS PASSED SUCCESSFULLY ".center(80, "="))

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")

    print("=" * 80 + "\n")
