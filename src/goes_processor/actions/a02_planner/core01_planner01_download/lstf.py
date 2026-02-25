import s3fs
import os
import json
from datetime import datetime, timezone

def get_goes_satellite(year, day):
    """
    Determines the correct satellite based on the GOES-16 to GOES-19 
    transition which occurred around April 2025.
    """
    date_obj = datetime.strptime(f"{year}-{day}", "%Y-%j")
    
    # Transition Logic: GOES-19 became the primary East satellite in early 2025
    if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
        return "16"
    return "19"

def gen_plan_download_ONE_DAY_LSTF(year, day):
    # 1. Configuración básica
    sat = get_goes_satellite(year, day)
    day_str = str(day).zfill(3)
    product = "ABI-L2-LSTF"
    bucket = f"noaa-goes{sat}"
    
    try:
        date_obj = datetime.strptime(f"{year}-{day_str}", "%Y-%j")
        date_gregorian = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return f"Error: Day {day_str} is invalid for year {year}."

    # 2. Contenedor: Información del Producto (Estático)
    prod_info = {
        "satellite": f"GOES-{sat}",
        "product": product,
        "bucket": bucket,
        "year": year,
        "day": day_str,
        "date_julian": f"{year}{day_str}",  
        "date_gregorian": date_gregorian,
        "resolution": "2km"
    }

    # 3. Contenedor: Información del Planificador (Metadatos del JSON)
    planner_download_info = {
        "file_name": None,           # Se inyecta en el CLI
        "path_relative": None,       # Se inyecta en el CLI
        "path_absolute": None,       # Se inyecta en el CLI
    }

    # 4. Inicializar el inventario de archivos
    inventory_files = {}
    
    hours = [f"{h:02d}" for h in range(24)]
    minutes = ["00"]  # LSTF suele ser horario
    total_slots = len(hours) * len(minutes)
    counter = 1
    
    for h_str in hours:
        for m_str in minutes:
            # Timestamp usado en nombres de archivos GOES
            time_id = f"{year}{day_str}{h_str}{m_str}"
            s_time = f"s{time_id}"
            file_key = f"file{str(counter).zfill(2)}"
            
            # Patrón de búsqueda en S3
            regex_pattern = f"{bucket}/{product}/{year}/{day_str}/{h_str}/OR_ABI-L2-LSTF*{s_time}*.nc"
            
            inventory_files[file_key] = {
                "pos_file": f"{str(counter).zfill(2)} of {str(total_slots).zfill(2)}",
                "year": year,
                "day": day_str,
                "hour": h_str,
                "minutes": m_str,
                "s_time": s_time,
                "regex": regex_pattern,
                "file_name": None,
                "path_relative": None,
                "path_absolute": None,
                "file_exist_local": False,
                "file_size_mb_web": None,
                "file_size_mb_local": None,
                "is_check": False
            }
            counter += 1
            
    # --- BLOQUE DE RESUMEN (Summary) ---
    # Este bloque debe estar alineado con los diccionarios anteriores
    summary_info = {
        "is_done": False,
        "total_files": None,           
        "total_time": None,       
        "total_size_mb": None,      
        "time_file_creation": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System time",
        "time_last_mod": None
    }
    
    # 5. Retorno del Diccionario Unificado
    return {
        "prod_info": prod_info,
        "planner_download_info": planner_download_info,
        "summary": summary_info,
        "download_files": inventory_files
    }
