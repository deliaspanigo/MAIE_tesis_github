"""
Path: src/goes_processor/__init__.py
Version: 0.1.9 (Task 02 Focused)
"""

MY_NAME = "goes_processor/__init__.py"
__version__ = "0.1.9"

try:
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM ERROR] - Critical core failure in {MY_NAME}: {e}\n")
    raise SystemExit(1)

def get_version():
    """Retorna la versión actual del procesador."""
    return f"GOES-Processor Tool v.{__version__}"
