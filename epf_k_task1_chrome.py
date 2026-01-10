import asyncio
import json
from pathlib import Path
from base64 import b64encode

from playwright.async_api import async_playwright


PX_TO_PT = 72 / 96  # CSS px to PDF points (Chrome uses 96 CSS px per inch)

def font_face_css(family: str, ttf_path: Path) -> str:
    data_b64 = b64encode(ttf_path.read_bytes()).decode("ascii")
    return f"""
    @font-face {{
      font-family: "{family}";
      src: url(data:font/ttf;base64,{data_b64}) format("truetype");
      font-weight: 400;
      font-style: normal;
    }}
    """

def build_html(font_dir: Path) -> str:
    # Embed fonts directly into HTML so rendering is deterministic.
    css_fonts = "\n".join([
        font_face_css("NotoSans", font_dir / "NotoSans-Regular.ttf"),
        font_face_css("NotoSansSinhala", font_dir / "NotoSansSinhala-Regular.ttf"),
        font_face_css("NotoSansTamil", font_dir / "NotoSansTamil-Regular.ttf"),
    ])

    # NOTE: Replace label strings with exact official EPF Form K text when needed full fidelity.
    si_label = "සාමාජිකයාගේ සම්පූර්ණ නම"
    ta_label = "உறுப்பினரின் முழுப்பெயர்"
    en_label = "Full Name of member"

    # Use A4 size and zero margins for clean coordinate mapping.
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
{css_fonts}

@page {{
  size: A4;
  margin: 0;
}}

html, body {{
  width: 210mm;
  height: 297mm;
  margin: 0;
  padding: 0;
  background: white;
}}

.page {{
  position: relative;
  width: 210mm;
  height: 297mm;
  box-sizing: border-box;
}}

.header {{
  position: absolute;
  left: 12mm;
  right: 12mm;
  top: 10mm;
  text-align: center;
  color: #000;
}}

.header .small {{
  font-family: "NotoSans";
  font-size: 9pt;
  text-align: left;
}}

.header .si {{
  font-family: "NotoSansSinhala";
  font-size: 12pt;
  margin-top: 8mm;
}}

.header .ta {{
  font-family: "NotoSansTamil";
  font-size: 11pt;
  margin-top: 1.5mm;
}}

.header .en {{
  font-family: "NotoSans";
  font-size: 12pt;
  margin-top: 1.5mm;
}}

.header .formid {{
  font-family: "NotoSansSinhala";
  font-size: 11pt;
  margin-top: 6mm;
}}

.field1 {{
  position: absolute;
  left: 12mm;
  right: 12mm;
  top: 70mm;
  color: #000;
  display: flex;
  align-items: flex-start;
  gap: 6mm;
}}

.field1 .num {{
  font-family: "NotoSans";
  font-size: 10pt;
  line-height: 1.2;
  width: 6mm;
}}

.field1 .label {{
  width: 70mm;
}}

.field1 .label .si {{
  font-family: "NotoSansSinhala";
  font-size: 10pt;
  line-height: 1.2;
}}
.field1 .label .ta {{
  font-family: "NotoSansTamil";
  font-size: 10pt;
  line-height: 1.2;
  margin-top: 1.2mm;
}}
.field1 .label .en {{
  font-family: "NotoSans";
  font-size: 10pt;
  line-height: 1.2;
  margin-top: 1.2mm;
}}

.field1 .input {{
  flex: 1;
  margin-top: 8mm; /* aligns with 3rd label line visually */
  height: 7mm;
  border-bottom: 1px dotted #000;
}}

</style>
</head>

<body>
  <div class="page">
    <div class="header">
      <div class="small">ISSUED FREE OF CHARGE.</div>

      <div class="si">1958 අංක 15 දරණ සේවක අර්ථසාධක අරමුදල් පනත</div>
      <div class="ta">1958 ஆம் ஆண்டு 15 ஆம் இல. ஊழியர் சேமலாப நிதி சட்டம்</div>
      <div class="en">THE EMPLOYEES' PROVIDENT FUND ACT, No. 15 OF 1958</div>

      <div class="formid">“කේ” ආකෘතිය / “K” FORM</div>
    </div>

    <div class="field1">
      <div class="num">1.</div>

      <div class="label">
        <div class="si">{si_label}</div>
        <div class="ta">{ta_label}</div>
        <div class="en">{en_label}</div>
      </div>

      <!-- Ground-truth target: input area -->
      <div class="input" data-gt="field1_name_input"></div>
    </div>
  </div>
</body>
</html>
"""


async def main(out_pdf: str, out_json: str, font_dir: str):
    font_dir_p = Path(font_dir)

    required = [
        font_dir_p / "NotoSans-Regular.ttf",
        font_dir_p / "NotoSansSinhala-Regular.ttf",
        font_dir_p / "NotoSansTamil-Regular.ttf",
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing font: {p}")

    html = build_html(font_dir_p)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Set viewport close to A4 at 96dpi to keep coordinate mapping stable.
        # A4 inches: 8.27 x 11.69 -> px: 794 x 1123 (approx)
        await page.set_viewport_size({"width": 794, "height": 1123})

        await page.set_content(html, wait_until="load")

        # Wait for fonts to load (critical for correct shaping/metrics)
        await page.evaluate("() => document.fonts.ready")

        # Extract bbox in CSS pixels (top-left origin)
        bbox_px = await page.evaluate("""
        () => {
          const el = document.querySelector('[data-gt="field1_name_input"]');
          const r = el.getBoundingClientRect();
          return { x: r.x, y: r.y, width: r.width, height: r.height };
        }
        """)

        # Convert to PDF points (pt)
        bbox_pt = {
            "x": round(bbox_px["x"] * PX_TO_PT, 2),
            "y": round(bbox_px["y"] * PX_TO_PT, 2),
            "width": round(bbox_px["width"] * PX_TO_PT, 2),
            "height": round(bbox_px["height"] * PX_TO_PT, 2),
        }

        # Print PDF (A4, no margins)
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
            prefer_css_page_size=True,
        )
        Path(out_pdf).write_bytes(pdf_bytes)

        labels = {
            "schema_version": "formir.v1.minlabel",
            "document": {
                "doc_id": Path(out_pdf).stem,
                "origin": "top-left",
                "units": {"bbox_px": "css_px", "bbox_pt": "pt"},
                "labels": [
                    {
                        "id": "field1_name_input",
                        "type": "input_area",
                        "page_index": 0,
                        "bbox_px": [
                            round(bbox_px["x"], 2),
                            round(bbox_px["y"], 2),
                            round(bbox_px["width"], 2),
                            round(bbox_px["height"], 2),
                        ],
                        "bbox_pt": [
                            bbox_pt["x"], bbox_pt["y"], bbox_pt["width"], bbox_pt["height"]
                        ],
                    }
                ],
            },
        }
        Path(out_json).write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")

        await browser.close()

    print("Wrote:", out_pdf)
    print("Wrote:", out_json)
    print("Input bbox (pt):", labels["document"]["labels"][0]["bbox_pt"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_pdf", default="epf_k_task1.pdf")
    ap.add_argument("--out_json", default="epf_k_task1.labels.json")
    ap.add_argument("--font_dir", default="fonts")
    args = ap.parse_args()
    asyncio.run(main(args.out_pdf, args.out_json, args.font_dir))
