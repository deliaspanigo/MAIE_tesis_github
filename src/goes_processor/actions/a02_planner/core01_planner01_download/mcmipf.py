# src/goes_processor/actions/a02_planner/core01_p01_download/mcmipf.py

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

def gen_plan_download_ONE_DAY_MCMIPF(year, day):
    # 1. Configuración básica
    sat = get_goes_satellite(year, day)
    day_str = str(day).zfill(3)
    product = "ABI-L2-MCMIPF"
    bucket = f"noaa-goes{sat}"
   
    # 2. Convertir Día Juliano a Fecha Gregoriana (YYYY-MM-DD)
    try:
        date_obj = datetime.strptime(f"{year}-{day_str}", "%Y-%j")
        date_gregorian = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return f"Error: Day {day_str} is invalid for year {year}."

    # 3. Contenedor: Información del Producto (prod_info)
    prod_info = {
        "satellite": f"GOES-{sat}",
        "product": product,
        "bucket": bucket,
        "year": year,
        "day": day_str,
        "date_julian": f"{year}{day_str}",  # Formato YYYYDDD
        "date_gregorian": date_gregorian,
        "resolution": "2km"
    }

    # 4. Contenedor: Información del Planificador (planner_download_info)
    planner_download_info = {
        "file_name": None,           # Se inyecta en el CLI
        "path_relative": None,       # Se inyecta en el CLI
        "path_absolute": None,       # Se inyecta en el CLI
        "is_done": False,
        "time_file_creation": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System time",
        "time_last_mod": None
    }
    
    # 5. Inicializar inventario de archivos (Frecuencia: cada 10 min)
    inventory_files = {}
    hours = [f"{h:02d}" for h in range(24)]
    minutes = [f"{m:02d}" for m in range(0, 60, 10)] # 00, 10, 20, 30, 40, 50
    
    total_slots = len(hours) * len(minutes) # 144 archivos
    counter = 1
    
    for h_str in hours:
        for m_str in minutes:
            # Timestamp usado en los nombres de archivo de la NOAA
            time_id = f"{year}{day_str}{h_str}{m_str}"
            s_time = f"s{time_id}"
            
            # Usamos zfill(3) para manejar hasta 144 archivos correctamente
            file_key = f"file{str(counter).zfill(3)}"
            
            # Patrón de búsqueda para S3
            regex_pattern = f"{bucket}/{product}/{year}/{day_str}/{h_str}/OR_ABI-L2-MCMIPF*{s_time}*.nc"
            
            inventory_files[file_key] = {
                "pos_file": f"{str(counter).zfill(3)} of {str(total_slots).zfill(3)}",
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
                "file_size_mb_web": None,
                "is_check": False
            }
            counter += 1
            
    # 6. Retorno del Diccionario Unificado
    return {
        "prod_info": prod_info,
        "planner_download_info": planner_download_info,
        "download_files": inventory_files
    }
