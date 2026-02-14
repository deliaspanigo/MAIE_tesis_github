# src/goes_processor/download/download.py

import fsspec
from pathlib import Path
import os
import shutil
from typing import List
import socket
import time
from datetime import datetime

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def download_files(
    product: str,
    year: str,
    day_of_year: str, 
    hour: str,
    minute: str = "all",
    output_dir: str = "data/raw",
    satellite: str = "19",
    overwrite: bool = False
) -> List[Path]:
    
    start_time_process = time.time()
    system_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[*] Inicio del sistema: {system_start_time}")
    
    if not check_internet():
        print("\n" + "!"*60 + "\n[!] ERROR: SIN ACCESO A INTERNET.\n" + "!"*60)
        return []

    bucket_name = f"noaa-goes{satellite}"
    fs = fsspec.filesystem('s3', anon=True)
    
    path_prefix = f"{bucket_name}/{product}/{year}/{day_of_year.zfill(3)}"
    if hour != "all":
        path_prefix += f"/{hour.zfill(2)}"

    print(f"[*] Escaneando: s3://{path_prefix}")
    
    try:
        all_files = fs.glob(f"{path_prefix}/**/*.nc")
    except Exception as e:
        print(f"[!] Error al acceder al bucket: {e}")
        return []

    if minute != "all":
        time_match = f"s{year}{day_of_year.zfill(3)}{hour.zfill(2)}{minute.zfill(2)}"
        files_to_download = [f for f in all_files if time_match in f]
    else:
        files_to_download = all_files

    total_files = len(files_to_download)
    if total_files == 0:
        print(f"[!] No se encontraron archivos.")
        return []

    print(f"[*] Se encontraron {total_files} archivos.")

    # --- LÓGICA DE PADDING PARA EL CONTADOR (01/24) ---
    padding = len(str(total_files))
    if padding < 2: padding = 2  # Mínimo siempre 2 dígitos (01)

    downloaded_paths = []
    
    for i, remote_file in enumerate(files_to_download, 1):
        filename = remote_file.split('/')[-1]
        h_folder = remote_file.split('/')[-2]
        
        local_path = Path(output_dir) / bucket_name / product / year / day_of_year.zfill(3) / h_folder / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        remote_size = fs.size(remote_file)
        
        # Formateo del contador con ceros a la izquierda
        progress_label = f"[{i:0{padding}d}/{total_files:0{padding}d}]"

        # VERIFICACIÓN DE INTEGRIDAD
        if local_path.exists():
            local_size = local_path.stat().st_size
            if local_size == remote_size:
                if not overwrite:
                    print(f"   {progress_label} [OK - EXISTE] {filename} ({local_size/(1024**2):.1f} MB)")
                    downloaded_paths.append(local_path)
                    continue
            else:
                print(f"   {progress_label} [CORRUPTO] {local_size} != {remote_size}. Re-descargando...")
                local_path.unlink()

        # DESCARGA
        print(f"   {progress_label} [BAJANDO] {filename}...")
        try:
            with fs.open(remote_file, 'rb') as rf, open(local_path, 'wb') as lf:
                shutil.copyfileobj(rf, lf)
            
            if local_path.stat().st_size == remote_size:
                print(f"         └─> [DONE] {local_path.stat().st_size/(1024**2):.1f} MB")
                downloaded_paths.append(local_path)
            else:
                print(f"         └─> [!] ERROR: Tamaño final incorrecto.")
        except Exception as e:
            print(f"         └─> [!] ERROR DE RED: {e}")
            if local_path.exists(): local_path.unlink()

    print(f"\n[*] PROCESO FINALIZADO en {(time.time() - start_time_process)/60:.2f} min")
    return downloaded_paths
