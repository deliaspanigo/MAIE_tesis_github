

# ALL GOES - ALL PRODUCTS - ALL PROCESSES
goes-processor planning gen-plan            --product ALL --year 2026 --day 003 --sat-position ALL --save True --overwrite True --check-local True
goes-processor planning check-plan-download --product ALL --year 2026 --day 003 --sat-position ALL

# G19 - east - ALL PRODUCTS
goes-processor planning gen-plan-download   --sat-position east  --product ALL --year 2026 --day 003  --save True --overwrite True --check-local True
goes-processor planning check-plan-download --sat-position east  --product ALL --year 2026 --day 003 
goes-processor download run-download        --sat-position east  --product ALL --year 2026 --day 003 --hour 10 --minute ALL --overwrite False
goes-processor planning check-plan-download --sat-position east  --product ALL --year 2026 --day 003 

# G19 - east - ABI-L2-LSTF
goes-processor planning gen-plan-download   --sat-position east  --product ABI-L2-LSTF --year 2026 --day 003  --overwrite True --check-local True
goes-processor planning check-plan-download --sat-position east  --product ABI-L2-LSTF --year 2026 --day 003 
goes-processor download run-download        --sat-position east  --product ABI-L2-LSTF --year 2026 --day 003 --hour 10 --minute ALL --overwrite False
goes-processor planning check-plan-download --sat-position east  --product ABI-L2-LSTF --year 2026 --day 003 
