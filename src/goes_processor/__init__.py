# src/goes_processor/__init__.py
__version__ = "0.3.1"

try:
    from .actions.download.core.download_goes_files import download_goes_files
    from .actions.processing.fns_folder.crawler import find_files
    from .actions.processing.core_01_one_file.lst import process_lst_single
    from .utils.logger import setup_legion_logger
except ImportError as e:
    print(f"[LEGION-INIT-WARNING] Dependency issue: {e}")
