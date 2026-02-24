# src/goes_processor/__init__.py
__version__ = "0.5.9"

try:
    # 1. Import the planner CLI (exposed as 'cli' in step 1)
    from .actions.a02_planner import cli as planner_cli
    
    # 2. Import the downloader CLI
    from .actions.a03_download.download_cli import cli as download_cli
    
    # 3. Logger
    from .utils.logger import setup_legion_logger

except ImportError as e:
    # This keeps your warning but only triggers on real missing files
    print(f"[LEGION-INIT-WARNING] Dependency issue: {e}")
