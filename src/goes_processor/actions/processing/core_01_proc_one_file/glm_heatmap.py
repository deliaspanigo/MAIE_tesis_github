# src/goes_processor/processing/logic_how/glm_heatmap.py

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter
from pathlib import Path
import rasterio
from rasterio.transform import from_origin

def process_heatmap(file_path, input_base, output_base, indent="    "):
    file_path = Path(file_path)
    input_base = Path(input_base).resolve()
    output_base = Path(output_base).resolve()
    
    # 1. LÓGICA DE CARPETAS IDENTICA A LST (Carpeta por Archivo)
    rel_path = file_path.relative_to(input_base)
    # Creamos la ruta: base / año / dia / hora / NOMBRE_DEL_ARCHIVO_NC /
    out_dir = output_base / rel_path.parent / file_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Extracción y Limpieza de Datos
    with nc.Dataset(file_path, 'r') as ds:
        lats = np.array(ds.variables['flash_lat'][:]).flatten()
        lons = np.array(ds.variables['flash_lon'][:]).flatten()
        mask = np.isfinite(lats) & np.isfinite(lons)
        lats, lons = lats[mask], lons[mask]
        lons = np.where(lons > 180, lons - 360, lons)

    # Preparación del Grid 3600x1800 (WGS84)
    lon_bins = np.linspace(-180, 180, 3601)
    lat_bins = np.linspace(-90, 90, 1801)
    heatmap, _, _ = np.histogram2d(lons, lats, bins=[lon_bins, lat_bins])
    h_map = gaussian_filter(heatmap.T, sigma=3.0)
    h_map = np.where(h_map < 0.001, np.nan, h_map)

    # ==========================================================
    # PRODUCTO 1: PNG Global WGS84 (3600x1800)
    # ==========================================================
    fig_wgs84 = plt.figure(figsize=(20, 10), facecolor='black')
    ax_wgs84 = plt.axes(projection=ccrs.PlateCarree())
    ax_wgs84.set_facecolor('black')
    ax_wgs84.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=0.5, zorder=3)
    
    if lons.size > 0:
        ax_wgs84.pcolormesh(lon_bins, lat_bins, h_map, cmap='magma', transform=ccrs.PlateCarree(), zorder=4)
    
    ax_wgs84.set_global()
    png_wgs84_path = out_dir / f"{file_path.stem}_WGS84.png"
    fig_wgs84.savefig(png_wgs84_path, facecolor='black', bbox_inches='tight', dpi=150)
    plt.close(fig_wgs84)

    # ==========================================================
    # PRODUCTO 2: GeoTIFF WGS84 (Data Científica)
    # ==========================================================
    tif_wgs84_path = out_dir / f"{file_path.stem}_DATA_WGS84.tif"
    transform = from_origin(-180, 0.1, 90, 0.1)
    data_to_save = np.flipud(np.nan_to_num(h_map))
    
    with rasterio.open(
        tif_wgs84_path, 'w', driver='GTiff',
        height=1800, width=3600, count=1,
        dtype='float32', crs='EPSG:4326',
        transform=transform, nodata=0
    ) as dst:
        dst.write(data_to_save.astype('float32'), 1)

    # ==========================================================
    # PRODUCTO 3: PNG GOES CRS (Proyección del Satélite)
    # ==========================================================
    sat_lon = -75.0 if any(x in file_path.name for x in ["G16", "G19"]) else -137.0
    goes_crs = ccrs.Geostationary(central_longitude=sat_lon)
    
    fig_goes = plt.figure(figsize=(12, 12), facecolor='black')
    ax_goes = plt.axes(projection=goes_crs)
    ax_goes.set_facecolor('black')
    ax_goes.add_feature(cfeature.COASTLINE, edgecolor='cyan', linewidth=0.8, zorder=2)
    ax_goes.add_feature(cfeature.BORDERS, edgecolor='white', linewidth=0.4, alpha=0.5)

    if lons.size > 0:
        ax_goes.scatter(lons, lats, color='orange', s=15, alpha=0.9, 
                        transform=ccrs.PlateCarree(), zorder=5)
    
    ax_goes.set_global()
    png_goes_path = out_dir / f"{file_path.stem}_GOES_CRS.png"
    fig_goes.savefig(png_goes_path, facecolor='black', bbox_inches='tight', dpi=150)
    plt.close(fig_goes)

    print(f"{indent}✅ Carpeta creada: {out_dir.name}")
    print(f"{indent}📸 [3 PRODUCTOS] guardados en subdirectorio.")
    return png_wgs84_path
