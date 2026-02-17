# src/goes_processor/utils/logger.py
import logging
from pathlib import Path
from datetime import datetime

def setup_legion_logger(name: str):
    # Crear carpeta de logs dentro de reports si no existe
    log_dir = Path("reports/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"legion_{name}_{timestamp}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formato con timestamp, nivel de error y mensaje
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    
    # Handler para escribir en archivo
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger, log_file
