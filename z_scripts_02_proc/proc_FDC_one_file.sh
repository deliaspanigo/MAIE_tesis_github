# Procesar un día completo (ejemplo: Año 2026, Día 003)
goes-processor processing one-file \
    --satellite 16 \
    --product ABI-L2-FDCF \
    --year 2026 \
    --day 003 \
    --hour all \
    --minute all \
    --input-dir data_raw/goes_raw \
    --output-dir data_processed \
    --overwrite False