# Version: v.0.4.9 - Core 02 CLI: Strict Julian Day & FDC Integration (English Version)

import click
import time
import itertools
import re
from pathlib import Path

# Import accumulation processors
from .core_02_proc_accumulation.glm_accumulation import process_glm_heatmap_list_file
from .core_02_proc_accumulation.fdc_accumulation import process_fdc_accumulation_list

# --- 1. STRICT JULIAN DAY VALIDATOR ---
def validate_julian_day(ctx, param, value):
    """Enforces that the day is exactly 3 digits (001-366)."""
    if not re.match(r'^\d{3}$', value):
        raise click.BadParameter('Day must be exactly 3 digits (e.g., 003 instead of 3).')
    day_int = int(value)
    if not (1 <= day_int <= 366):
        raise click.BadParameter('Day must be between 001 and 366.')
    return value

# --- 2. HELPER: BATCHING LOGIC ---
def group_files_by_bin(files, bin_type):
    """Segments the file list into groups based on the time interval."""
    if bin_type == "10minutes":
        # Group by Year+Day+Hour + First digit of the minute
        key_func = lambda f: f.name.split('_s')[1][:10] 
    elif bin_type == "01hour":
        # Group by Year+Day+Hour
        key_func = lambda f: f.name.split('_s')[1][:9]
    elif bin_type == "01day":
        # Group by Year+Day
        key_func = lambda f: f.name.split('_s')[1][:7]
    else:
        # Safety fallback: return everything as a single block
        return [files]

    groups = []
    # Sorting is vital for groupby to work correctly
    for _, group in itertools.groupby(sorted(files), key_func):
        groups.append(list(group))
    return groups

# --- 3. HELPER: VALIDATION & SEARCH ---
def validate_and_prepare_universe(satellite, product, year, day, hour, minute, input_dir):
    """Identifies the product and collects the initial file universe."""
    PRODUCT_MAP = {
        "LCFA": process_glm_heatmap_list_file,
        "FDC": process_fdc_accumulation_list,
    }

    # Identify processing function
    process_func = next((func for key, func in PRODUCT_MAP.items() if key in product.upper()), None)
    if not process_func:
        return None, None, f"❌ Product '{product}' is not supported for accumulation (Core 02)."

    input_base = Path(input_dir)
    # Search using the validated 3-digit 'day'
    search_path = f"**/OR_{product}*G{satellite}_s{year}{day}*"
    files = sorted(list(input_base.glob(search_path)))
    
    # Time filtering
    if hour.lower() != 'all':
        files = [f for f in files if f.name.split('_s')[1][7:9] == hour.zfill(2)]
    if minute.lower() != 'all':
        files = [f for f in files if f.name.split('_s')[1][9:11] == minute.zfill(2)]

    if not files:
        return None, None, f"❌ No files found for {product} on Day:{day} H:{hour} M:{minute}"

    return files, process_func, None


# --- 4. CLI COMMAND ---
@click.command(name="accumulate")
@click.option('--satellite', type=str, required=True, help="Satellite number (16, 17, 18, 19)")
@click.option('--product', type=str, required=True, help="Product (e.g., GLM-L2-LCFA or ABI-L2-FDCF)")
@click.option('--year', type=str, required=True)
@click.option('--day', type=str, required=True, callback=validate_julian_day, help="Julian day (DDD, e.g. 003)")
@click.option('--hour', type=str, required=True, help="HH or 'all'")
@click.option('--minute', type=str, required=True, help="MM or 'all'")
@click.option('--bin', 
              type=click.Choice(['10minutes', '01hour', '01day']), 
              required=True, 
              help="Aggregation interval")
@click.option('--input-dir', type=click.Path(exists=True), required=True)
@click.option('--output-dir', type=click.Path(), required=True)
@click.option('--overwrite', 
              type=click.Choice(['True', 'False']), 
              required=True, 
              help="Force re-processing of existing files?")
def proc_accumulation_cmd(satellite, product, year, day, hour, minute, bin, input_dir, output_dir, overwrite):
    """
    v.0.4.9 - GOES-R Temporal Accumulator (Core 02).
    Groups the selected universe of files into time bins and processes each as a batch.
    """
    
    # Convert mandatory string choice to real Boolean
    ovw_bool = True if overwrite == "True" else False

    # STEP A: Discovery
    files, process_func, error_msg = validate_and_prepare_universe(
        satellite, product, year, day, hour, minute, input_dir
    )
    
    if error_msg:
        click.echo(error_msg)
        return

    # STEP B: Batch Segmentation
    batches = group_files_by_bin(files, bin)
    total_batches = len(batches)
    padding = len(str(total_batches))
    processed_count = 0
    start_ts = time.time()
    
    output_base = Path(output_dir)

    click.echo(f"\n🚀 Core 02: Found {len(files)} files in universe.")
    click.echo(f"📦 Segmented into {total_batches} batches of {bin}...\n")

    # STEP C: Execution Loop over Batches
    for i, batch in enumerate(batches, 1):
        idx_str = str(i).zfill(padding)
        # Time label for logging (HHMM from the first file in the batch)
        batch_label = batch[0].name.split('_s')[1][7:11] 
        click.echo(f"[{idx_str}/{total_batches}] Accumulating batch starting at: {batch_label} ({len(batch)} files)")
        
        try:
            # Call processing engine
            success_report = process_func(
                file_list=batch,
                output_base=output_base,
                time_bin=bin,
                satellite=f"G{satellite}",
                overwrite=ovw_bool,
                indent="    "
            )
            
            if all(success_report.values()):
                processed_count += 1
            else:
                failed_stages = [k for k, v in success_report.items() if not v]
                click.echo(f"    ⚠️  Partial failure in batch stages: {failed_stages}")

        except Exception as e:
            click.echo(f"    ❌ Critical failure in batch {i}: {e}")

    # STEP D: Final Summary
    duration = time.time() - start_ts
    click.echo("\n" + "="*50)
    click.echo(f"✅ Summary: {processed_count}/{total_batches} batches fully completed.")
    click.echo(f"⏱️  Total duration: {int(duration // 60)} min {int(duration % 60)} sec")
    click.echo("="*50 + "\n")
