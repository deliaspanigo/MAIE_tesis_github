# src/goes_processor/__init__.py
__version__ = "0.3.1"

try:
    # Importaciones de descarga
    from .actions.download.core.download_goes_files import download_goes_files
    
    # Importaciones de procesamiento (Crawler)
    from .actions.processing.fns_folder.crawler import find_files
    
    # CORRECCIÓN: Apuntamos directamente a la lógica en la carpeta del core, 
    # evitando el archivo CLI que causaba el conflicto de nombres.
    from .actions.processing.core_01_proc_one_file.lst import process_lst_single_file
    
    # Utilidades
    from .utils.logger import setup_legion_logger

except ImportError as e:
    # Este print es el que generaba el aviso en rojo en tu consola
    print(f"[LEGION-INIT-WARNING] Dependency issue: {e}")
