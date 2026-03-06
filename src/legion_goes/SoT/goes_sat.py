"""
FILE PATH: src/legion_goes/SoT/goes_sat.py
Version: 0.4.1 (Historical Aware Logic)
"""

from types import MappingProxyType
from datetime import datetime
import re

# ===================================================================
# CONFIGURACIÓN Y TRANSICIONES HISTÓRICAS
# ===================================================================
AVAILABLE_GOES_SAT_POSITIONS = ("east", "west")

# Fechas exactas de cambio de satélite operacional (Source: NOAA)
TRANSITIONS = {
    "east_16_to_19": datetime(2025, 2, 10), # Fecha estimada de cambio operacional del G19
    "west_17_to_18": datetime(2023, 1, 4),   # Fecha real del cambio operacional del G18
    "east_13_to_16": datetime(2017, 12, 18)  # Por si procesas datos muy viejos
}

_PRIVATE_SAT_INFO = {
    "16": {"bucket": "noaa-goes16", "name01": "16", "name06": "GOES16", "default_position": "east"},
    "17": {"bucket": "noaa-goes17", "name01": "17", "name06": "GOES17", "default_position": "west"},
    "18": {"bucket": "noaa-goes18", "name01": "18", "name06": "GOES18", "default_position": "west"},
    "19": {"bucket": "noaa-goes19", "name01": "19", "name06": "GOES19", "default_position": "east"}
}

SAVED_INFO_SAT_GOES = MappingProxyType({
    k: MappingProxyType(v) for k, v in _PRIVATE_SAT_INFO.items()
})

# ===================================================================
# LÓGICA DE RESOLUCIÓN
# ===================================================================

def get_goes_id_by_date(year: str, day: str, sat_position: str) -> str:
    """
    Determina qué satélite era el activo en una posición y fecha dadas.
    """
    date_obj = datetime.strptime(f"{year}-{str(day).zfill(3)}", "%Y-%j")
    pos = str(sat_position).lower()

    if pos == "east":
        # Antes de Feb 2025 era el 16, después el 19
        if date_obj < TRANSITIONS["east_16_to_19"]:
            return "16"
        else:
            return "19"
            
    elif pos == "west":
        # Antes de Enero 2023 era el 17, después el 18
        if date_obj < TRANSITIONS["west_17_to_18"]:
            return "17"
        else:
            return "18"
            
    raise ValueError(f"Posición desconocida: {sat_position}")

def get_sat_info(sat_id_or_pos: str, year: str = None, day: str = None) -> dict:
    """
    RESOLVER UNIVERSAL: 
    Si pasas 'east' y una fecha, busca el satélite de esa época.
    """
    val = str(sat_id_or_pos).lower().replace("goes", "").replace("-", "").strip()

    # 1. Si es un ID numérico directo, lo usamos
    if val in ("16", "17", "18", "19"):
        real_id = val
    # 2. Si es una posición, requerimos fecha para saber cuál era el activo
    elif val in AVAILABLE_GOES_SAT_POSITIONS:
        if not year or not day:
            # Si no hay fecha, usamos hoy como fallback, pero avisamos o manejamos
            now = datetime.now()
            year, day = now.strftime("%Y"), now.strftime("%j")
        
        real_id = get_goes_id_by_date(year, day, val)
    else:
        raise ValueError(f"No se puede resolver satélite para: {sat_id_or_pos}")

    info = SAVED_INFO_SAT_GOES[real_id]
    return {
        "id": info["name01"],
        "pos": info["default_position"].upper(),
        "bucket": info["bucket"],
        "name06": info["name06"]
    }
