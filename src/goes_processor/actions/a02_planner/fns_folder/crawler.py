from pathlib import Path

def find_files(base_dir, satellite, product, year, day, hour, minute):
    """
    Busca archivos de forma inteligente filtrando por satélite, producto y tiempo.
    """
    base_path = Path(base_dir).resolve()
    sat_folder = f"noaa-goes{satellite}"
    
    # 1. Buscamos TODOS los archivos .nc dentro de la carpeta del satélite y producto
    # Usamos rglob para que no importe la estructura de carpetas (año/día/hora)
    all_files = list(base_path.glob(f"{sat_folder}/**/{product}/*.nc"))
    
    # Si no hay carpeta del producto, intentamos en la raíz del satélite
    if not all_files:
        all_files = list(base_path.glob(f"{sat_folder}/**/*.nc"))

    matched_files = []
    
    # 2. Filtramos por el nombre del archivo (Patrón: ..._sYYYYJJJHHMM...)
    # Ejemplo: OR_ABI-L2-MCMIPF-M6_G19_s20250031500...
    
    # Construimos el "prefijo" de tiempo que buscamos
    # Si es 'all', lo dejamos vacío para que coincida con cualquier cosa
    y_filt = year if year != "all" else ""
    d_filt = day if day != "all" else ""
    h_filt = hour if hour != "all" else ""
    m_filt = minute if minute != "all" else ""
    
    time_match = f"_s{y_filt}{d_filt}{h_filt}{m_filt}"

    for f in all_files:
        if product in f.name and time_match in f.name:
            matched_files.append(f)

    return sorted(matched_files)
