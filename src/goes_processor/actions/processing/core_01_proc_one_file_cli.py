import click
from pathlib import Path
import time
from .core_01_proc_one_file.lst import process_lst_single_file

# --- 1. HELPER: VALIDATION & SEARCH ---
def validate_and_prepare(satellite, product, year, day, hour, minute, input_dir):
    """
    Validates user arguments and performs file crawling based on GOES-R standards.
    """
    PRODUCT_MAP = {
        "LST": process_lst_single_file,
        # "FDC": process_fdc_single_file,
    }

    # Resolve processing function
    process_func = next((func for key, func in PRODUCT_MAP.items() if key in product.upper()), None)
    if not process_func:
        return None, None, f"❌ Product '{product}' is not supported."

    # File Crawler with Scan Mode wildcard (M*)
    input_base = Path(input_dir)
    search_path = f"**/OR_{product}-M*G{satellite}_s{year}{day}*"
    files = sorted(list(input_base.glob(search_path)))
    
    # Time Filtering
    if hour.lower() != 'all':
        files = [f for f in files if f.name.split('_s')[1][7:9] == hour.zfill(2)]
    if minute.lower() != 'all':
        files = [f for f in files if f.name.split('_s')[1][9:11] == minute.zfill(2)]

    if not files:
        return None, None, f"❌ No files found for {product} on Day:{day} H:{hour} M:{minute}"

    return files, process_func, None


# --- 2. CLI COMMAND ---
@click.command(name="one-file")
@click.option('--satellite', type=str, required=True, help="Satellite number (e.g., 16, 19)")
@click.option('--product', type=str, required=True, help="Product (e.g., ABI-L2-LSTF)")
@click.option('--year', type=str, required=True)
@click.option('--day', type=str, required=True, help="Julian day (DDD)")
@click.option('--hour', type=str, required=True)
@click.option('--minute', type=str, required=True)
@click.option('--input-dir', type=click.Path(exists=True), required=True)
@click.option('--output-dir', type=click.Path(), required=True)
@click.option('--overwrite', type=click.BOOL, default=False)
def proc_single_file_cmd(satellite, product, year, day, hour, minute, input_dir, output_dir, overwrite):
    """
    v.0.0.1 - GOES-R Sequential Processor CLI.
    Orchestrates multiple processing stages and reports success per stage.
    """
    
    # STEP A: Validation
    files, process_func, error_msg = validate_and_prepare(
        satellite, product, year, day, hour, minute, input_dir
    )
    
    if error_msg:
        click.echo(error_msg)
        return

    # STEP B: Execution Loop
    total_files = len(files)
    padding = len(str(total_files))
    processed_count = 0
    start_ts = time.time()
    
    input_base = Path(input_dir)
    output_base = Path(output_dir)

    click.echo(f"\n🚀 Starting sequential pipeline for {total_files} files...\n")

    for i, file_path in enumerate(files, 1):
        idx_str = str(i).zfill(padding)
        click.echo(f"[{idx_str}/{total_files}] Processing: {file_path.name}")
        
        try:
            # The core function now returns a DICTIONARY of success statuses
            success_report = process_func(
                input_file=file_path,
                input_base=input_base,
                output_base=output_base,
                overwrite=overwrite,
                indent="    "
            )
            
            # Logic: File is "Processed" if ALL stages in the report are True
            if all(success_report.values()):
                processed_count += 1
            else:
                # Detail which stage failed for the user
                failed_stages = [k for k, v in success_report.items() if not v]
                click.echo(f"    ⚠️  Partial failure in stages: {failed_stages}")

        except Exception as e:
            click.echo(f"    ❌ Critical failure in orchestrator: {e}")

    # STEP C: Final Summary
    duration = time.time() - start_ts
    click.echo("\n" + "="*50)
    click.echo(f"✅ Summary: {processed_count}/{total_files} files fully completed.")
    click.echo(f"⏱️  Total duration: {int(duration // 60)} min {int(duration % 60)} sec")
    click.echo("="*50 + "\n")
