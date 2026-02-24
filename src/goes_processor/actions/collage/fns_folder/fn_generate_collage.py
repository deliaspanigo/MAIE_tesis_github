import time
import os
from PIL import Image
import matplotlib.pyplot as plt
from pathlib import Path

def fn_generate_collage(list_sat_images, list_bg_layers=None, list_top_layers=None, target_res=None, output_folder="output", show_result=True):
    """
    Multilevel image composition for satellite imagery with Notebook preview.
    Layers are stacked as: Background -> Satellite Data -> Top Overlays (Borders/Coastlines).
    """
    bg_layers = list_bg_layers or []
    top_layers = list_top_layers or []
    all_files = bg_layers + list_sat_images + top_layers

    if not all_files:
        print("❌ No files provided for processing.")
        return None

    # 1. Automatic Resolution Detection
    if target_res is None:
        max_w, max_h = 0, 0
        for p in all_files:
            if os.path.exists(p):
                with Image.open(p) as img:
                    w, h = img.size
                    if w > max_w: 
                        max_w, max_h = w, h
        target_res = (max_w, max_h)
    
    print(f"🚀 Composing at {target_res[0]}x{target_res[1]}...")

    # 2. Base Canvas Initialization
    canvas = Image.new("RGBA", target_res, (0, 0, 0, 0))

    # 3. Stack order: Background -> Satellite -> Borders/Coastlines
    processing_stack = [
        ("Background", bg_layers),
        ("Satellite", list_sat_images),
        ("Overlays", top_layers)
    ]

    for category, files in processing_stack:
        for p in files:
            if not os.path.exists(p):
                print(f"⚠️ File not found: {p}")
                continue
            
            print(f"🎨 [{category}] Processing: {Path(p).name}")
            with Image.open(p) as img:
                # Ensure the layer is in RGBA for proper transparency handling
                layer = img.convert("RGBA")
                
                # Resize if the layer doesn't match target resolution
                if layer.size != target_res:
                    layer = layer.resize(target_res, Image.Resampling.LANCZOS)
                
                # Composite the layer onto the canvas
                canvas = Image.alpha_composite(canvas, layer)

    # 4. Save result
    if not os.path.exists(output_folder): 
        os.makedirs(output_folder)
        
    output_filename = os.path.join(output_folder, f"fusion_{int(time.time())}.png")
    canvas.save(output_filename)
    print(f"✅ Composition saved to: {output_filename}")

    # 5. Notebook Preview
    if show_result:
        plt.figure(figsize=(12, 8))
        plt.imshow(canvas)
        plt.axis('off')
        plt.title(f"Preview: {target_res[0]}x{target_res[1]}", fontsize=10)
        plt.show()

    return canvas
