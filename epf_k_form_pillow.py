"""
Synthetic Data Generator: V2 (Pillow Method)
Renders Sinhala/Tamil text as images to ensure correct shaping (ligatures).
Output:
- PDF (Visuals are perfect images of text)
- JSON (Ground Truth Bounding Boxes)
"""

import os
import json
import argparse
import io
from dataclasses import dataclass
from typing import Dict, Tuple, List

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Helpers: Coordinate System
# ----------------------------

@dataclass(frozen=True)
class Page:
    width: float
    height: float

def tl_to_rl(page: Page, x: float, y: float, h: float = 0) -> Tuple[float, float]:
    """Convert top-left coords (x,y) to ReportLab bottom-left coords."""
    return (x, page.height - (y + h))

def draw_dotted_line_tl(c: canvas.Canvas, page: Page,
                        x1: float, y: float, x2: float,
                        stroke_width: float = 0.9) -> None:
    """Draw a dotted/dashed horizontal line."""
    c.saveState()
    c.setLineWidth(stroke_width)
    c.setDash(1, 2)
    rx1, ry = tl_to_rl(page, x1, y, 0)
    rx2, _ = tl_to_rl(page, x2, y, 0)
    c.line(rx1, ry, rx2, ry)
    c.restoreState()

# ----------------------------
# The Magic: Pillow Text Renderer
# ----------------------------

def draw_text_as_image(c: canvas.Canvas, page: Page, x: float, y: float, text: str,
                       font_path: str, font_size_pt: float,
                       align: str = "left", text_color=(0, 0, 0)) -> Tuple[float, float, float, float]:
    """
    Renders text using Pillow (for correct Indic shaping) and places it on the PDF.
    Returns the bbox [x, y, w, h] in PDF points (top-left origin).
    """
    
    # 1. Setup Scaling (Draw high-res then downscale for crisp PDF)
    scale_factor = 4  
    font_size_px = int(font_size_pt * 1.333 * scale_factor) # Approx pt to px conversion
    
    try:
        font = ImageFont.truetype(font_path, font_size_px)
    except OSError:
        print(f"ERROR: Could not load font at {font_path}")
        return (x, y, 0, 0)

    # 2. Measure Text Size
    # getbbox returns (left, top, right, bottom) of the rendered glyphs
    dummy_img = Image.new('RGBA', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    left, top, right, bottom = dummy_draw.textbbox((0, 0), text, font=font)
    
    text_w_px = right - left
    text_h_px = bottom - top
    
    # Add a little padding so letters don't get clipped
    img_w = text_w_px + int(10 * scale_factor)
    img_h = text_h_px + int(10 * scale_factor)

    # 3. Draw Text to Transparent Image
    img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    # Draw text offset by -left/-top to align tightly to 0,0
    draw.text((-left, -top), text, font=font, fill=text_color)

    # 4. Convert Pixels back to PDF Points
    pdf_w = img_w / (1.333 * scale_factor)
    pdf_h = img_h / (1.333 * scale_factor)
    
    # 5. Calculate Alignment Position
    if align == "center":
        x_final = x - (pdf_w / 2.0)
    elif align == "right":
        x_final = x - pdf_w
    else:
        x_final = x
        
    y_final = y  # Top-left Y

    # 6. Place on PDF
    # Save PIL image to memory buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # ReportLab ImageReader
    from reportlab.lib.utils import ImageReader
    rl_img = ImageReader(img_buffer)
    
    # Convert to RL coords
    rx, ry = tl_to_rl(page, x_final, y_final, pdf_h)
    
    # Draw the image
    c.drawImage(rl_img, rx, ry, width=pdf_w, height=pdf_h, mask='auto')

    return (x_final, y_final, pdf_w, pdf_h)

# ----------------------------
# Configuration & Content
# ----------------------------

def get_font_paths(font_dir: str) -> Dict[str, str]:
    """Map language codes to exact file paths."""
    return {
        "EN": os.path.join(font_dir, "NotoSans-Regular.ttf"),
        "SI": os.path.join(font_dir, "NotoSansSinhala-Regular.ttf"),
        "TA": os.path.join(font_dir, "NotoSansTamil-Regular.ttf"),
    }

def draw_header(c: canvas.Canvas, page: Page, fonts: Dict[str, str]) -> None:
    """Draws the trilingual header."""
    center_x = page.width / 2.0
    
    draw_text_as_image(c, page, 50, 40, "ISSUED FREE OF CHARGE.", fonts["EN"], 9)
    
    # Sinhala Title
    draw_text_as_image(c, page, center_x, 80, 
                       "1958 අංක 15 දරණ සේවක අර්ථසාධක අරමුදල් පනත", 
                       fonts["SI"], 12, align="center")
    
    # Tamil Title
    draw_text_as_image(c, page, center_x, 100, 
                       "1958 ஆம் ஆண்டு 15 ஆம் இல. ஊழியர் சேமலாப நிதி சட்டம்", 
                       fonts["TA"], 10, align="center")
                       
    # English Title
    draw_text_as_image(c, page, center_x, 120, 
                       "THE EMPLOYEES' PROVIDENT FUND ACT, No. 15 OF 1958", 
                       fonts["EN"], 11, align="center")

    # Form ID
    draw_text_as_image(c, page, center_x, 150, 
                       "“කේ” ආකෘතිය / “K” FORM", 
                       fonts["SI"], 11, align="center")

def draw_field1(c: canvas.Canvas, page: Page, fonts: Dict[str, str]) -> Dict:
    """Draws Field 1 and returns the Input Area label."""
    start_y = 220
    left_margin = 50
    
    # "1."
    draw_text_as_image(c, page, left_margin, start_y, "1.", fonts["EN"], 10)
    
    # Labels
    label_x = left_margin + 20
    draw_text_as_image(c, page, label_x, start_y, "සාමාජිකයාගේ සම්පූර්ණ නම", fonts["SI"], 10)
    draw_text_as_image(c, page, label_x, start_y + 15, "உறுப்பினரின் முழுப்பெயர்", fonts["TA"], 10)
    draw_text_as_image(c, page, label_x, start_y + 30, "Full Name of member", fonts["EN"], 10)
    
    # Dotted Line
    line_start_x = label_x + 200
    line_end_x = page.width - 50
    line_y = start_y + 40
    
    draw_dotted_line_tl(c, page, line_start_x, line_y, line_end_x)
    
    # Define the "Input Area" Bounding Box (for AI Labeling)
    return {
        "id": "field_1_name",
        "type": "input_area",
        "bbox": [round(line_start_x, 2), round(line_y - 15, 2), 
                 round(line_end_x - line_start_x, 2), 20]
    }

# ----------------------------
# Main Execution
# ----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_pdf", default="epf_k_fixed.pdf")
    ap.add_argument("--out_json", default="epf_k_labels.json")
    ap.add_argument("--font_dir", default="fonts")
    args = ap.parse_args()

    fonts = get_font_paths(args.font_dir)
    
    # Validate fonts exist
    for lang, path in fonts.items():
        if not os.path.exists(path):
            print(f"CRITICAL: Missing font for {lang} at {path}")
            return

    # Setup PDF
    page_w, page_h = A4
    page = Page(width=page_w, height=page_h)
    c = canvas.Canvas(args.out_pdf, pagesize=A4)

    # Draw Elements
    draw_header(c, page, fonts)
    label_data = draw_field1(c, page, fonts)

    c.showPage()
    c.save()

    # Save Labels
    final_json = {
        "document": "EPF_K_FORM",
        "page_size": [page_w, page_h],
        "labels": [label_data]
    }
    
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2)

    print(f"Success! Created {args.out_pdf} with correct text shaping.")

if __name__ == "__main__":
    main()