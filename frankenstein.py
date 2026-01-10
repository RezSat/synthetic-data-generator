import asyncio
import json
import random
import os
from pathlib import Path
from base64 import b64encode
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
PX_TO_PT = 72 / 96  # CSS px to PDF points conversion

# --- 1. FONT HANDLING (Your Robust Base64 Logic) ---
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

# --- 2. RANDOM CONTENT GENERATORS (The "Lego Blocks") ---
# We use simple placeholders to teach the AI structure.

TEXT_SI = "ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජයේ ආණ්ඩුක්‍රම ව්‍යවස්ථාව"
TEXT_TA = "இலங்கை சனநாயக சோசலிசக் குடியரசின் அரசியலமைப்பு"
TEXT_EN = "The Constitution of the Democratic Socialist Republic of Sri Lanka"

def get_random_text(length_multiplier=1):
    base = f"{TEXT_SI} {TEXT_EN} {TEXT_TA}. "
    return base * length_multiplier

def block_header(id_num):
    """Generates a Centered Header Block"""
    return f"""
    <div class="layout-box header" data-label="header" data-id="{id_num}" 
         style="text-align: center; margin-bottom: 20px;">
        <h2 style="font-family: 'NotoSansSinhala', 'NotoSans'; margin: 0;">
            {TEXT_SI[:20]}... (HEADER)
        </h2>
        <div style="font-size: 10pt; color: #555;">ID: {random.randint(1000, 9999)}</div>
    </div>
    """

def block_paragraph(id_num):
    """Generates a Text Block"""
    return f"""
    <div class="layout-box paragraph" data-label="text_block" data-id="{id_num}" 
         style="margin-bottom: 15px; text-align: justify; font-size: 11pt; line-height: 1.4;">
        {get_random_text(random.randint(2, 5))}
    </div>
    """

def block_key_value(id_num):
    """Generates a Form Input Field (Name: ......)"""
    label_si = "සම්පූර්ණ නම"
    label_en = "Full Name"
    return f"""
    <div class="layout-box input_row" data-label="key_value_pair" data-id="{id_num}"
         style="display: flex; margin-bottom: 15px; align-items: flex-end;">
        <div style="width: 35%; font-weight: bold; font-size: 11pt;">
            <div>{label_si}</div>
            <div style="font-size: 9pt;">{label_en}</div>
        </div>
        <div style="flex-grow: 1; border-bottom: 1px dotted #000; height: 30px;"></div>
    </div>
    """

def block_table(id_num):
    """Generates a Grid/Table"""
    rows = ""
    for r in range(random.randint(2, 4)):
        cols = ""
        for c in range(3):
            cols += f'<td style="border: 1px solid #000; padding: 5px;">Data {r}-{c}</td>'
        rows += f"<tr>{cols}</tr>"
    
    return f"""
    <div class="layout-box table" data-label="table" data-id="{id_num}" 
         style="margin-bottom: 20px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 10pt;">
            {rows}
        </table>
    </div>
    """

# --- 3. PAGE COMPOSER ---
def build_random_page_html(font_dir: Path) -> str:
    css_fonts = get_base_css(font_dir)
    
    # Randomly select blocks to build the page
    blocks = []
    block_generators = [block_paragraph, block_key_value, block_table, block_key_value]
    
    # Always start with a header
    blocks.append(block_header(0))
    
    # Add 4-6 random blocks
    for i in range(1, random.randint(5, 7)):
        gen_func = random.choice(block_generators)
        blocks.append(gen_func(i))
    
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
}}
/* Visual border for debugging (optional, AI doesn't need it if capturing layout) */
/* .layout-box {{ border: 1px dashed #ccc; }} */
</style>
</head>
<body>
  <div class="page">
    {body_content}
  </div>
</body>
</html>
"""

# --- 4. MAIN GENERATOR LOOP ---
async def generate_dataset(output_dir: str, font_dir: str, count: int):
    font_dir_p = Path(font_dir)
    out_dir_p = Path(output_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    
    # Subfolders for clean organization
    (out_dir_p / "pdfs").mkdir(exist_ok=True)
    (out_dir_p / "labels").mkdir(exist_ok=True)
    (out_dir_p / "images").mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Fixed viewport for consistent rendering
        await page.set_viewport_size({"width": 794, "height": 1123})

        for i in range(count):
            # A. Build HTML
            html = build_random_page_html(font_dir_p)
            await page.set_content(html, wait_until="load")
            await page.evaluate("() => document.fonts.ready")

            # B. Extract Labels (Auto-Labeling)
            # We find every element with class 'layout-box' and get its info
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

            # Convert PX to PT for PDF coordinates
            processed_labels = []
            for item in labels_data:
                px = item['bbox_px']
                processed_labels.append({
                    "id": item['id'],
                    "class": item['class'],
                    "bbox_px": [round(px['x'], 2), round(px['y'], 2), round(px['width'], 2), round(px['height'], 2)],
                    "bbox_pt": [
                        round(px['x'] * PX_TO_PT, 2),
                        round(px['y'] * PX_TO_PT, 2),
                        round(px['width'] * PX_TO_PT, 2),
                        round(px['height'] * PX_TO_PT, 2)
                    ]
                })

            # C. Save Outputs
            file_stem = f"sample_{i:04d}"
            
            # 1. PDF (The Document)
            pdf_path = out_dir_p / "pdfs" / f"{file_stem}.pdf"
            await page.pdf(path=pdf_path, format="A4", margin={"top":"0","bottom":"0","left":"0","right":"0"})
            
            # 2. Image (The Input for Vision AI)
            img_path = out_dir_p / "images" / f"{file_stem}.png"
            await page.screenshot(path=img_path, full_page=True)

            # 3. JSON (The Ground Truth)
            json_path = out_dir_p / "labels" / f"{file_stem}.json"
            label_file = {
                "file": f"{file_stem}.png",
                "image_size": [794, 1123],
                "annotations": processed_labels
            }
            json_path.write_text(json.dumps(label_file, ensure_ascii=False, indent=2), encoding="utf-8")

            print(f"Generated: {file_stem} ({len(processed_labels)} elements)")

        await browser.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5, help="How many samples to generate")
    ap.add_argument("--out_dir", default="dataset_v1", help="Output folder")
    ap.add_argument("--font_dir", default="fonts", help="Folder with TTF files")
    args = ap.parse_args()
    
    asyncio.run(generate_dataset(args.out_dir, args.font_dir, args.count))