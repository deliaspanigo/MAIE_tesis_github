# src/goes_processor/config_satpy.py
"""
Centralized configuration file for global Satpy settings.
v.0.0.1 - Centralized Cache Configuration
"""

import satpy
from pathlib import Path
import os

# 1. Define ABSOLUTE paths
# BASE_DIR points to the location of this config file
BASE_DIR = Path(__file__).resolve().parent
# ROOT_DIR points to the project root
ROOT_DIR = BASE_DIR.parent.parent

# Single definition for the cache directory
CACHE_DIR = ROOT_DIR / "my_satpy_cache_resampling" 
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Directory for custom YAML configurations (composites, enhancements, etc.)
custom_config_dir = BASE_DIR / "satpy_configs"

# 2. Global Satpy Configuration
# We force the use of str(CACHE_DIR) to ensure compatibility across different OS
satpy.config.set(
    cache_dir=str(CACHE_DIR),
    log_level="WARNING",
    default_resampler="kd_tree",  # Optimized for cache reuse
    config_path=[str(custom_config_dir)] 
)

# 3. FORCE ENVIRONMENT VARIABLE FOR PYRESAMPLE
# Critical for the resampling engine to write .zarr/.nc files into the correct folder
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 4. Startup Verification Message
print(f"--- SatPy Configuration (v.0.0.1) ---")
print(f"✅ Cache linked to: {CACHE_DIR}")
print(f"  - Resampler: {satpy.config.get('default_resampler')}")
print(f"---------------------------------------")
