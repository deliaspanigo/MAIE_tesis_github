# src/goes_processor/__init__.py
__version__ = "0.3.1"

try:
    from .actions.download.core.download_goes_files import download_goes_files
    from .actions.processing.fns_folder.crawler import find_files
    
    # IMPORTANTE: Agregamos MCMIP aquí también
    from .actions.processing.core_01_proc_one_file.lst import process_lst_single_file
    from .actions.processing.core_01_proc_one_file.mcmip_truecolor import process_mcmip_true_color_single_file
    
    from .utils.logger import setup_legion_logger

except ImportError as e:
    print(f"[LEGION-INIT-WARNING] Dependency issue: {e}")
