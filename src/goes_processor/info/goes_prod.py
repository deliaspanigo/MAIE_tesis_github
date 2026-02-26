# src/goes_processor/goes_info/goes_prod.py

"""
Standardized and up-to-date information for GOES-R ABI/GLM products (Level 2 Full Disk and others).
Last update: February 2026 (based on current NOAA/GOES-R documentation).

Official sources:
- NOAA GOES-R Series Data Book: https://www.goes-r.gov/downloads/resources/documents/GOES-R_Series_Data_Book.pdf
- ABI Level 2 Product Guide: https://www.star.nesdis.noaa.gov/GOES/ABI_docs/ABI_L2_Product_Guide.pdf
- GLM Level 2 Product Guide: https://www.star.nesdis.noaa.gov/GOES/GOES_GLM_L2_Product_Guide.pdf
- GOES-R ABI Scan Modes and Cadences: https://www.goes-r.gov/products/docs/PUG-L2+-vol5.pdf
"""

from types import MappingProxyType
from pathlib import Path

# ===================================================================
# REQUIRED KEYS (obligatory for ALL products)
# ===================================================================
REQUIRED_KEYS = {
    "full_name",
    "description",
    "level",
    "units",
    "typical_range",
    "main_use",
    "notes",
    "total_files_one_day",
    "time_lapse",
    "time_lapse_label",
    "type"
}

# ===================================================================
# REQUIRED RASTER KEYS (only for raster-based products)
# ===================================================================
REQUIRED_RASTER_KEYS = {
    "cadence_full_disk",
    "cadence_conus",
    "cadence_mesoscale",
    "resolution_nominal",
    "shape_full_disk"
}

# ===================================================================
# ALLOWED EXTRA KEYS FOR VECTORIAL PRODUCTS
# ===================================================================
ALLOWED_EXTRA_VECTORIAL_KEYS = {
    "cadence",
    "cadence_grouped",
    "resolution_spatial",
    "shape"
}

# ===================================================================
# PRIVATE SOURCE OF TRUTH (mutable only here)
# ===================================================================
_PRIVATE_PRODUCTS = {
    "ABI-L2-LSTF": {
        "full_name": "Land Surface Temperature (Full Disk)",
        "description": "Land Surface Temperature product",
        "level": "L2",
        "units": "Kelvin (original) → Celsius (post-processed)",
        "typical_range": "-100 °C to +100 °C (surface-dependent)",
        "main_use": "Drought monitoring, vegetation thermal stress, urban heat islands",
        "notes": "Requires atmospheric correction and surface emissivity. Values outside disk = fill (NaN or -9999).",
        "total_files_one_day": 24,
        "time_lapse": "01hour",
        "time_lapse_label": "time_lapse_01hour",
        "type": "raster",
        "cadence_full_disk": "10 minutes (Scan Mode 6, current default since 2019)",
        "cadence_conus": "5 minutes",
        "cadence_mesoscale": "60 seconds (or 30 seconds in alternate mode)",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424)
    },

    "ABI-L2-MCMIPF": {
        "full_name": "Multi-Channel Cloud and Moisture Imagery Product (Full Disk)",
        "description": "Multi-channel cloud and moisture imagery (pre-calculated reflectances and BT)",
        "level": "L2",
        "units": "Reflectance (0–1 or 0–100%), BT in Kelvin",
        "typical_range": "Reflectance 0–1, BT 180–340 K",
        "main_use": "Cloud, moisture, aerosol monitoring, True Color, derived RGBs",
        "notes": "Base for many RGB products (true_color, day_cloud_convection, etc.).",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "cadence_conus": "5 minutes",
        "cadence_mesoscale": "60 seconds",
        "resolution_nominal": "2 km (some bands 0.5 km or 1 km)",
        "shape_full_disk": (5424, 5424)
    },

    "ABI-L2-FDCF": {
        "full_name": "Fire Detection and Characterization (Full Disk)",
        "description": "Fire/hot spot detection and characterization",
        "level": "L2",
        "units": "Power (MW), Temp (K), Area (m²)",
        "typical_range": "Power 0–10,000 MW, Temp 300–1500 K",
        "main_use": "Early fire detection, agricultural burning monitoring",
        "notes": "Point-based dataset (not continuous image). Confidence mask 0–15.",
        "total_files_one_day": 144,
        "time_lapse": "10minutes",
        "time_lapse_label": "time_lapse_10minutes",
        "type": "raster",
        "cadence_full_disk": "10 minutes",
        "cadence_conus": "5 minutes",
        "cadence_mesoscale": "60 seconds",
        "resolution_nominal": "2 km",
        "shape_full_disk": (5424, 5424)
    },

    "GLM-L2-LCFA": {
        "full_name": "Lightning Cluster File (Level 2)",
        "description": "Lightning detection (events, groups, and flashes)",
        "level": "L2",
        "units": "Energy (J), Time (seconds since 2000-01-01)",
        "typical_range": "Energy 10⁻⁶ to 10³ J per flash",
        "main_use": "Storm monitoring, lightning activity, nowcasting",
        "notes": "Non-continuous image. Dataset of events/groups/flashes.",
        "total_files_one_day": 4320,
        "time_lapse": "20seconds",
        "time_lapse_label": "time_lapse_20seconds",
        "type": "vectorial",
        "cadence": "Packets every 20 seconds",
        "cadence_grouped": "Flashes grouped every 15 minutes (UTC-aligned windows)",
        "resolution_spatial": "Non-raster → geolocated points",
        "shape": "Variable (points per packet)"
    }
}

# ===================================================================
# AUTOMATIC VALIDATION ON MODULE IMPORT
# ===================================================================
def _validate_products():
    for product_id, data in _PRIVATE_PRODUCTS.items():
        # Common keys required for ALL
        missing_common = REQUIRED_KEYS - data.keys()
        if missing_common:
            raise ValueError(
                f"CRITICAL ERROR loading GOES products:\n"
                f"Product '{product_id}' is missing required keys:\n"
                f" → {', '.join(missing_common)}\n"
                f"File: {Path(__file__).resolve()}\n"
                f"Action: Add missing required keys."
            )

        # Raster-specific keys required only for raster products
        if data.get("type") == "raster":
            missing_raster = REQUIRED_RASTER_KEYS - data.keys()
            if missing_raster:
                raise ValueError(
                    f"CRITICAL ERROR loading GOES products:\n"
                    f"Raster product '{product_id}' is missing required keys:\n"
                    f" → {', '.join(missing_raster)}\n"
                    f"File: {Path(__file__).resolve()}\n"
                    f"Action: Add missing raster keys."
                )

        # Vectorial products: allow specific extra keys
        if data.get("type") == "vectorial":
            extra_allowed = data.keys() - REQUIRED_KEYS
            invalid_extra = extra_allowed - ALLOWED_EXTRA_VECTORIAL_KEYS
            if invalid_extra:
                raise ValueError(
                    f"CRITICAL ERROR loading GOES products:\n"
                    f"Vectorial product '{product_id}' has invalid extra keys:\n"
                    f" → {', '.join(invalid_extra)}\n"
                    f"Allowed extra keys for vectorial: {', '.join(ALLOWED_EXTRA_VECTORIAL_KEYS)}\n"
                    f"File: {Path(__file__).resolve()}\n"
                    f"Action: Remove invalid keys or add to ALLOWED_EXTRA_VECTORIAL_KEYS."
                )

        # Raster products: no extra keys allowed
        if data.get("type") == "raster":
            all_allowed = REQUIRED_KEYS | REQUIRED_RASTER_KEYS
            extra = data.keys() - all_allowed
            if extra:
                raise ValueError(
                    f"CRITICAL ERROR loading GOES products:\n"
                    f"Raster product '{product_id}' has extra keys (not allowed):\n"
                    f" → {', '.join(extra)}\n"
                    f"File: {Path(__file__).resolve()}\n"
                    f"Action: Remove extra keys."
                )

# Run validation immediately
_validate_products()

# ===================================================================
# PROTECTED, READ-ONLY PUBLIC INTERFACE
# ===================================================================
GOES_PRODUCTS = MappingProxyType({
    k: MappingProxyType(v) if isinstance(v, dict) else v
    for k, v in _PRIVATE_PRODUCTS.items()
})

# ===================================================================
# LIST OF AVAILABLE PRODUCTS (for CLI choices)
# ===================================================================
AVAILABLE_PRODUCTS = list(GOES_PRODUCTS.keys()) + ["ALL"]

# ===================================================================
# Helper to print product info
# ===================================================================
def print_product_info(product_id: str):
    if product_id not in GOES_PRODUCTS:
        print(f"Product '{product_id}' not found.")
        return
    
    info = GOES_PRODUCTS[product_id]
    print(f"\n=== {product_id} ===")
    for key, value in info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
