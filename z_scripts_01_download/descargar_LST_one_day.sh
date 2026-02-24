goes-processor download goes-files \
    --satellite 19 \
    --product ABI-L2-LSTF \
    --year 2026 \
    --day 003 \
    --hour all \
    --minute all \
    --overwrite no \
    --output-dir data_raw/goes_raw





goes-processor planner gen-plan-download --product ALL --year 2026 --day 003 --output-dir data_planner/p01_download --overwrite True


goes-processor download goes-files \
    --satellite 19 \
    --product ABI-L2-LSTF \
    --year 2026 \
    --day 003 \
    --overwrite no \
    --output-dir data_raw/goes_raw


goes-processor download run-plan-download --product ALL --year 2026 --day 003 --hour ALL --minute ALL \
                                          --planner-dir data_planner/p01_download --output-dir data_raw/goes_raw \
                                          --overwrite False --check-again True

goes-processor download run-plan-download --product GLM-L2-LCFA --year 2026 --day 003 --hour ALL --minute ALL --planner-dir data_planner/p01_download --output-dir data_raw/goes_raw --overwrite True --check-again False


goes-processor download run-plan-download --product GLM-L2-LCFA --year 2026 --day 003 --hour 00 --minute ALL --planner-dir data_planner/p01_download --output-dir data_raw/goes_raw --overwrite True --check-again False



goes-processor download run-plan-download --product ABI-L2-LSTF --year 2026 --day 003 --hour ALL --minute ALL \  
                                          --planner-dir data_planner/p01_download --output-dir data_raw/goes_raw --check-again False

goes-processor download run-plan-download --product ALL --year 2026 --day 003 --hour 00 --minute ALL --planner-dir data_planner/p01_download --output-dir data_raw/goes_raw --check-again False
