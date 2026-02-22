

tree -L 3

source venv/bin/activate


# Asegúrate de estar en ~/bulk/MAIE_tesis2026/f01_code/LEGION
pip uninstall goes-processor goes19_processor LEGION -y
pip install -e .

pip install -e . --no-cache-dir



goes-processor download goes-files \
    --satellite 19 \
    --product ABI-L2-LSTF \
    --year 2025 \
    --day 040 \
    --hour 18 \
    --overwrite no




./z_scripts_01_download/descargar_LSTF_one_day.sh


./z_scripts_01_download/descargar_MCMIPF_one_day.sh


./z_scripts_02_proc/proc_lst_one_file.sh




pip freeze > requirements_$(date +%Y%m%d_%H%M%S).txt

