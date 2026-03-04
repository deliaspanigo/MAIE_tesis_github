# =============================================================================
# FILE PATH: src/goes_processor/actions/a02_planning/__init__.py
# Version: 0.1.8 (Package Exposure & Integrity)
# =============================================================================

MY_NAME = "a02_planning/__init__.py"

# 1. CAPA DE SISTEMA
try:
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM ERROR] - In {MY_NAME}: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO (Exposición de interfaces)
try:
    # Exponemos el CLI principal para que sea importable desde la raíz
    from .a02_planning_cli import planning_group
    
    # Exponemos funciones core de core01 para acceso rápido (Shortcut)
    from .core01_planner_download.code01_gen_plan_download import generate_download_plan_day
    from .core01_planner_download.code02_check_plan_download import check_dict_download_plan_day
    
except ImportError as e:
    print("\n" + "="*80)
    print(f" [PROJECT LIB ERROR] - File: {MY_NAME}")
    print(f" Failed to initialize planning package: {e}")
    print("="*80 + "\n")
    # No levantamos SystemExit aquí para permitir que el error suba 
    # y se identifique el origen en el traceback.
    raise
