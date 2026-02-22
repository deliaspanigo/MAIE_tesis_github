# Procesar un día completo (ejemplo: Año 2026, Día 003)
goes-processor processing one-file \
    --satellite 19 \
    --product ABI-L2-FDCF \
    --year 2026 \
    --day 003 \
    --hour all \
    --minute all \
    --input-dir data_raw/goes_raw \
    --output-dir data_processed/core_01_proc_one_file \
    --overwrite False