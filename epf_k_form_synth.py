"""
Synthetic Data Generator: 01
Synthetic EPF Form K (partial): Header + Field 1 (Name)
- ReportLab PDF output
- JSON sidecar with bounding box for "Input Area" of Field 1

Coordinate convention for JSON:
- origin: TOP-LEFT
- bbox: [x, y, width, height]
- units: PDF points (pt), 1pt = 1/72 inch
"""

import os
import json
import argparse
from dataclasses import dataclass
from typing import Dict, Tuple, List

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ----------------------------
# Helpers: coordinate system
# ----------------------------

@dataclass(frozen=True)
class Page:
    width: float
    height: float

def tl_to_rl(page: Page, x: float, y: float, h: float = 0) -> Tuple[float, float]:
    """
    Convert top-left coords (x,y) to ReportLab bottom-left coords.
    If placing a bbox, pass its height h to align top-left correctly.
    """
    return (x, page.height - (y + h))

def draw_text_tl(c: canvas.Canvas, page: Page, x: float, y: float, text: str,
                 font_name: str, font_size: float,
                 align: str = "left") -> Tuple[float, float, float, float]:
    """
    Draw single-line text using top-left origin.
    Returns an approximate bbox [x, y, w, h] in top-left coords.
    """
    c.setFont(font_name, font_size)
    w = pdfmetrics.stringWidth(text, font_name, font_size)
    h = font_size * 1.2  # approximate line box

    if align == "left":
        x0 = x
    elif align == "center":
        x0 = x - (w / 2.0)
    elif align == "right":
        x0 = x - w
    else:
        raise ValueError("align must be left/center/right")

    rx, ry = tl_to_rl(page, x0, y, h)
    c.drawString(rx, ry, text)
    return (x0, y, w, h)

def draw_dotted_line_tl(c: canvas.Canvas, page: Page,
                        x1: float, y: float, x2: float,
                        stroke_width: float = 0.9,
                        dot_on: float = 1.0, dot_off: float = 2.0) -> None:
    """
    Draw a dotted/dashed horizontal line at top-left y.
    """
    c.saveState()
    c.setLineWidth(stroke_width)
    c.setDash(dot_on, dot_off)
    rx1, ry = tl_to_rl(page, x1, y, 0)
    rx2, _ = tl_to_rl(page, x2, y, 0)
    c.line(rx1, ry, rx2, ry)
    c.restoreState()

def draw_rect_tl(c: canvas.Canvas, page: Page,
                 x: float, y: float, w: float, h: float,
                 stroke_width: float = 1.0) -> None:
    """
    Draw rectangle using top-left origin.
    """
    c.saveState()
    c.setLineWidth(stroke_width)
    rx, ry = tl_to_rl(page, x, y, h)
    c.rect(rx, ry, w, h, stroke=1, fill=0)
    c.restoreState()


# ----------------------------
# Fonts
# ----------------------------

def register_fonts(font_dir: str) -> Dict[str, str]:
    """
    Registers required fonts and returns mapping:
      { "EN": <fontName>, "SI": <fontName>, "TA": <fontName> }

    Expected files in font_dir:
      - NotoSans-Regular.ttf
      - NotoSansSinhala-Regular.ttf
      - NotoSansTamil-Regular.ttf
    """
    font_files = {
        "EN": ("NotoSans", "NotoSans-Regular.ttf"),
        "SI": ("NotoSansSinhala", "NotoSansSinhala-Regular.ttf"),
        "TA": ("NotoSansTamil", "NotoSansTamil-Regular.ttf"),
    }

    out = {}
    for k, (family, filename) in font_files.items():
        path = os.path.join(font_dir, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"Missing font file: {path}\n"
                f"Put the required Noto fonts into: {font_dir}\n"
                f"Needed: {list(v[1] for v in font_files.values())}"
            )
        pdfmetrics.registerFont(TTFont(family, path))
        out[k] = family

    return out


# ----------------------------
# Drawing: Header + Field 1
# ----------------------------

def draw_header(c: canvas.Canvas, page: Page, fonts: Dict[str, str]) -> None:
    """
    Simple tri-lingual header block (approximate).
    Adjust text/positions to match your exact EPF K scan if needed.
    """
    left_margin = 50
    center_x = page.width / 2.0

    # Top note (English)
    draw_text_tl(c, page, left_margin, 40, "ISSUED FREE OF CHARGE.", fonts["EN"], 9)

    # Main title lines (center)
    draw_text_tl(c, page, center_x, 85,
                 "1958 අංක 15 දරණ සේවක අර්ථසාධක අරමුදල් පනත",
                 fonts["SI"], 12, align="center")
    draw_text_tl(c, page, center_x, 103,
                 "1958 ஆம் ஆண்டு 15 ஆம் இல. ஊழியர் சேமலாப நிதி சட்டம்",
                 fonts["TA"], 11, align="center")
    draw_text_tl(c, page, center_x, 123,
                 "THE EMPLOYEES' PROVIDENT FUND ACT, No. 15 OF 1958",
                 fonts["EN"], 12, align="center")

    # Form identifier (center)
    draw_text_tl(c, page, center_x, 150,
                 "“කේ” ආකෘතිය / “K” FORM",
                 fonts["SI"], 11, align="center")


def draw_field1_name(c: canvas.Canvas, page: Page, fonts: Dict[str, str]) -> Dict:
    """
    Field 1: label (Sinhala/Tamil/English stacked) + dotted input line.
    Returns label record for JSON.
    """
    left_margin = 50
    right_margin = 50

    # Field block position (top-left coords)
    top_y = 235

    # "1." number
    draw_text_tl(c, page, left_margin, top_y, "1.", fonts["EN"], 10)

    # Label block (stacked 3 lines)
    label_x = left_margin + 22
    label_y = top_y - 2
    line_gap = 12  # vertical spacing between label lines (pt)

    # NOTE: Replace these strings with the exact official translations you want.
    si = "සාමාජිකයාගේ සම්පූර්ණ නම"
    ta = "உறுப்பினரின் முழுப்பெயர்"
    en = "Full Name of member"

    draw_text_tl(c, page, label_x, label_y + 0 * line_gap, si, fonts["SI"], 10)
    draw_text_tl(c, page, label_x, label_y + 1 * line_gap, ta, fonts["TA"], 10)
    draw_text_tl(c, page, label_x, label_y + 2 * line_gap, en, fonts["EN"], 10)

    # Input line starts after label block
    label_block_w = 210  # tweak for your form
    input_x1 = label_x + label_block_w + 10
    input_x2 = page.width - right_margin

    # Align dotted line roughly with the EN label baseline region
    dotted_y = label_y + 2 * line_gap + 9  # adjust for aesthetic alignment

    draw_dotted_line_tl(c, page, input_x1, dotted_y, input_x2,
                        stroke_width=0.9, dot_on=1.0, dot_off=2.0)

    # Define "Input Area" bbox (top-left origin)
    # A thin line isn't a bbox; we define a practical writable region around it.
    input_h = 18.0
    input_y = dotted_y - (input_h / 2.0)
    input_w = (input_x2 - input_x1)

    # (Optional) Debug visual bounding box (comment out in production)
    # draw_rect_tl(c, page, input_x1, input_y, input_w, input_h, stroke_width=0.5)

    return {
        "id": "field1_name_input",
        "type": "input_area",
        "page_index": 0,
        "bbox": [round(input_x1, 2), round(input_y, 2), round(input_w, 2), round(input_h, 2)],
        "units": "pt",
        "origin": "top-left"
    }


# ----------------------------
# Main
# ----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_pdf", default="epf_form_k_header_field1.pdf")
    ap.add_argument("--out_json", default="epf_form_k_header_field1.labels.json")
    ap.add_argument("--font_dir", default="fonts",
                    help="Folder containing NotoSans-Regular.ttf, NotoSansSinhala-Regular.ttf, NotoSansTamil-Regular.ttf")
    args = ap.parse_args()

    fonts = register_fonts(args.font_dir)

    page_w, page_h = A4
    page = Page(width=page_w, height=page_h)

    c = canvas.Canvas(args.out_pdf, pagesize=A4)

    # Draw
    draw_header(c, page, fonts)
    label = draw_field1_name(c, page, fonts)

    c.showPage()
    c.save()

    # Sidecar JSON (Ground Truth)
    sidecar = {
        "schema_version": "formir.v1.minlabel",
        "document": {
            "doc_id": os.path.splitext(os.path.basename(args.out_pdf))[0],
            "page_size": [round(page.width, 2), round(page.height, 2)],
            "labels": [label]
        }
    }

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=2)

    print(f"Wrote PDF : {args.out_pdf}")
    print(f"Wrote JSON: {args.out_json}")
    print("Input Area bbox:", label["bbox"])


if __name__ == "__main__":
    main()
