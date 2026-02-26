goes-processor download goes-files \
    --satellite 19 \
    --product ABI-L2-LSTF \
    --year 2026 \
    --day 003 \
    --hour all \
    --minute all \
    --overwrite no \
    --output-dir data_raw/goes_raw




goes-processor planning gen-plan --product ALL --year 2026 --day 003 --sat-position ALL --save True --overwrite True --check-local True
goes-processor planning check-plan-download --product ALL --year 2026 --day 003 --sat-position ALL

# G19 - east
goes-processor planning gen-plan-download   --product ALL --year 2026 --day 003 --sat-position east --save True --overwrite True --check-local True
goes-processor planning check-plan-download --product ALL --year 2026 --day 003 --sat-position east


# G19 - east - ABI-L2-LSTF
goes-processor planning gen-plan-download   --product ABI-L2-LSTF --year 2026 --day 003 --sat-position east --save True --overwrite True --check-local True
goes-processor planning check-plan-download --product ABI-L2-LSTF --year 2026 --day 003 --sat-position east





goes-processor planning gen-plan --product ALL --year 2026 --day 003 --sat-position ALL --save True --overwrite True



goes-processor planning gen-plan   --product ALL --year 2026 --day 003 --sat-position ALL --overwrite True
goes-processor planning check-plan --product ALL --year 2026 --day 003 --sat-position ALL




goes-processor planner gen-plan-download  --product ALL --year 2026 --day 003 --overwrite True
goes-processor download run-plan-download --product ALL --year 2026 --day 003 --hour ALL --minute ALL  --overwrite False --check-again True


goes-processor planner gen-plan-processing --product ALL --year 2026 --day 003 --overwrite True


goes-processor processing run-each-file --product ABI-L2-LSTF --year 2026 --day 003 --overwrite False



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
