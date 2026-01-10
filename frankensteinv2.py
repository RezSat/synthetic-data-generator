import asyncio
import json
import random
import os
from pathlib import Path
from base64 import b64encode
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
PX_TO_PT = 72 / 96

# --- 1. FONT HANDLING ---
def font_face_css(family: str, ttf_path: Path) -> str:
    if not ttf_path.exists():
        raise FileNotFoundError(f"Missing font: {ttf_path}")
    data_b64 = b64encode(ttf_path.read_bytes()).decode("ascii")
    return f"""
    @font-face {{
      font-family: "{family}";
      src: url(data:font/ttf;base64,{data_b64}) format("truetype");
      font-weight: 400;
      font-style: normal;
    }}
    """

def get_base_css(font_dir: Path) -> str:
    return "\n".join([
        font_face_css("NotoSans", font_dir / "NotoSans-Regular.ttf"),
        font_face_css("NotoSansSinhala", font_dir / "NotoSansSinhala-Regular.ttf"),
        font_face_css("NotoSansTamil", font_dir / "NotoSansTamil-Regular.ttf"),
    ])

# --- 2. TEXT GENERATORS ---
TEXT_SI = "ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජයේ ආණ්ඩුක්‍රම ව්‍යවස්ථාව"
TEXT_TA = "இலங்கை சனநாயக சோசலிசக் குடியரசின் அரசியலமைப்பு"
TEXT_EN = "The Constitution of the Democratic Socialist Republic of Sri Lanka"

def get_random_text(length=1):
    return (f"{TEXT_SI} {TEXT_EN} {TEXT_TA}. " * length)[:random.randint(50, 200)]

# --- 3. ATOMIC BLOCKS (The Content) ---

def block_header(id_num):
    return f"""
    <div class="layout-box header" data-label="header" data-id="{id_num}" 
         style="text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px;">
        <h2 style="font-family: 'NotoSansSinhala'; margin: 0;">EPF FORM {random.randint(1,99)}</h2>
        <div style="font-size: 10pt;">GOVERNMENT OF SRI LANKA</div>
    </div>
    """

def block_paragraph(id_num):
    return f"""
    <div class="layout-box paragraph" data-label="text_block" data-id="{id_num}" 
         style="margin-bottom: 10px; text-align: justify; font-size: 10pt;">
        {get_random_text(random.randint(1, 3))}
    </div>
    """

def block_input_field(id_num):
    label = random.choice(["Full Name", "Address", "NIC Number", "Date of Birth"])
    return f"""
    <div class="layout-box input" data-label="key_value" data-id="{id_num}"
         style="margin-bottom: 10px;">
        <div style="font-weight: bold; font-size: 10pt;">{label}:</div>
        <div style="border-bottom: 1px dotted #000; height: 25px; background: #f9f9f9;"></div>
    </div>
    """

def block_checkbox_group(id_num):
    # Generates a list of 3 options
    items = ""
    for i in range(3):
        items += f"""
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 15px; height: 15px; border: 1px solid #000; margin-right: 10px;"></div>
            <div style="font-size: 10pt;">Option {chr(65+i)}: {get_random_text()[:20]}</div>
        </div>
        """
    return f"""
    <div class="layout-box checkbox_group" data-label="checkbox_group" data-id="{id_num}" 
         style="margin-bottom: 10px; padding: 5px;">
        {items}
    </div>
    """

def block_signature(id_num):
    return f"""
    <div class="layout-box signature" data-label="signature_area" data-id="{id_num}"
         style="margin-top: 20px; margin-bottom: 20px; width: 100%;">
        <div style="height: 40px; border-bottom: 1px solid #000;"></div>
        <div style="text-align: center; font-size: 9pt; margin-top: 5px;">Signature of Applicant</div>
    </div>
    """

# --- 4. LAYOUT MANAGERS (The "Containers") ---

def get_random_atomic_block(id_base):
    # Returns a random basic block
    generators = [block_paragraph, block_input_field, block_checkbox_group, block_input_field]
    gen = random.choice(generators)
    return gen(f"{id_base}_{random.randint(100,999)}")

def row_full_width(id_base):
    # 1 Column (Standard)
    return get_random_atomic_block(id_base)

def row_two_columns(id_base):
    # 2 Columns (50% / 50%)
    left = get_random_atomic_block(f"{id_base}_L")
    right = get_random_atomic_block(f"{id_base}_R")
    return f"""
    <div style="display: flex; gap: 20px; margin-bottom: 15px;">
        <div style="flex: 1;">{left}</div>
        <div style="flex: 1;">{right}</div>
    </div>
    """

def row_three_columns(id_base):
    # 3 Columns (33% each - good for checkboxes or short inputs)
    c1 = get_random_atomic_block(f"{id_base}_1")
    c2 = get_random_atomic_block(f"{id_base}_2")
    c3 = get_random_atomic_block(f"{id_base}_3")
    return f"""
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <div style="flex: 1;">{c1}</div>
        <div style="flex: 1;">{c2}</div>
        <div style="flex: 1;">{c3}</div>
    </div>
    """

# --- 5. PAGE COMPOSER ---
def build_random_page_html(font_dir: Path) -> str:
    css_fonts = get_base_css(font_dir)
    
    blocks = []
    
    # Always a Header
    blocks.append(block_header(0))
    
    # Add 5-8 Layout Rows (Some full, some split)
    layout_strategies = [row_full_width, row_full_width, row_two_columns, row_two_columns, row_three_columns]
    
    for i in range(1, random.randint(6, 9)):
        strategy = random.choice(layout_strategies)
        blocks.append(strategy(i))
    
    # Always end with Signature
    blocks.append(block_signature(99))

    body_content = "\n".join(blocks)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
{css_fonts}
@page {{ size: A4; margin: 0; }}
html, body {{ width: 210mm; height: 297mm; margin: 0; padding: 0; background: white; }}
.page {{ 
    padding: 20mm; 
    box-sizing: border-box; 
    font-family: 'NotoSans', 'NotoSansSinhala', 'NotoSansTamil', sans-serif;
    display: flex;
    flex-direction: column;
}}
</style>
</head>
<body>
  <div class="page">
    {body_content}
  </div>
</body>
</html>
"""

# --- 6. MAIN LOOP (Unchanged logic, just calling new builder) ---
async def generate_dataset(output_dir: str, font_dir: str, count: int):
    font_dir_p = Path(font_dir)
    out_dir_p = Path(output_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    (out_dir_p / "pdfs").mkdir(exist_ok=True)
    (out_dir_p / "labels").mkdir(exist_ok=True)
    (out_dir_p / "images").mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 794, "height": 1123})

        for i in range(count):
            html = build_random_page_html(font_dir_p)
            await page.set_content(html, wait_until="load")
            await page.evaluate("() => document.fonts.ready")

            # Extract Labels (Updated to catch nested layout-boxes)
            labels_data = await page.evaluate("""
            () => {
                const boxes = document.querySelectorAll('.layout-box');
                return Array.from(boxes).map(el => {
                    const r = el.getBoundingClientRect();
                    return {
                        id: el.getAttribute('data-id'),
                        class: el.getAttribute('data-label'),
                        bbox_px: { x: r.x, y: r.y, width: r.width, height: r.height }
                    };
                });
            }
            """)

            # Convert PX to PT
            processed_labels = []
            for item in labels_data:
                px = item['bbox_px']
                processed_labels.append({
                    "id": item['id'],
                    "class": item['class'],
                    "bbox_px": [round(px['x'], 2), round(px['y'], 2), round(px['width'], 2), round(px['height'], 2)],
                    "bbox_pt": [round(px['x'] * PX_TO_PT, 2), round(px['y'] * PX_TO_PT, 2), round(px['width'] * PX_TO_PT, 2), round(px['height'] * PX_TO_PT, 2)]
                })

            file_stem = f"complex_sample_{i:04d}"
            await page.pdf(path=out_dir_p / "pdfs" / f"{file_stem}.pdf", format="A4", margin={"top":"0","bottom":"0","left":"0","right":"0"})
            await page.screenshot(path=out_dir_p / "images" / f"{file_stem}.png", full_page=True)
            
            json_path = out_dir_p / "labels" / f"{file_stem}.json"
            label_file = {"file": f"{file_stem}.png", "image_size": [794, 1123], "annotations": processed_labels}
            json_path.write_text(json.dumps(label_file, ensure_ascii=False, indent=2), encoding="utf-8")

            print(f"Generated: {file_stem} (Labels: {len(processed_labels)})")

        await browser.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--out_dir", default="dataset_complex", help="Output folder")
    ap.add_argument("--font_dir", default="fonts", help="Folder with TTF files")
    args = ap.parse_args()
    asyncio.run(generate_dataset(args.out_dir, args.font_dir, args.count))