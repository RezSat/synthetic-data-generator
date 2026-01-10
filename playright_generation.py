import json
from playwright.sync_api import sync_playwright

# 1. The "Template" is just HTML. 
# Chrome already knows how to render Sinhala. I can just tell it where to put it.
html_content = """
<!DOCTYPE html>
<html>
<head>
<style>
    /* Import a nice font from Google so it works on any machine */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&display=swap');

    body { 
        font-family: 'Noto Sans Sinhala', sans-serif; 
        width: 210mm; height: 297mm; /* A4 size */
        margin: 0; padding: 0;
        position: relative;
    }

    /* We recreate the form layout using absolute positioning (pixel perfect) */
    .header {
        position: absolute; top: 30mm; width: 100%; text-align: center;
        font-size: 16px; font-weight: bold;
    }

    .field-label {
        position: absolute; left: 20mm; top: 80mm;
        font-size: 14px;
    }

    .field-input {
        position: absolute; left: 80mm; top: 92mm;
        width: 100mm; border-bottom: 2px dotted black;
    }
</style>
</head>
<body>
    <div class="header">
        1958 අංක 15 දරණ සේවක අර්ථසාධක අරමුදල් පනත<br>
        THE EMPLOYEES' PROVIDENT FUND ACT
    </div>

    <div id="lbl_name" class="field-label">
        1. සාමාජිකයාගේ සම්පූර්ණ නම (Sinhala Name Here)
    </div>

    <div id="input_name" class="field-input"></div>
</body>
</html>
"""

def create_perfect_form():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html_content)
        page.wait_for_load_state("networkidle") # Wait for fonts

        # --- AUTOMATIC LABELING ---
        # ask Chrome: "Where exactly did you draw the input box?"
        # Chrome gives us the EXACT coordinates. No math needed.
        bbox = page.locator("#input_name").bounding_box()

        page.pdf(path="final_form.pdf", format="A4", print_background=True)

        # Save the Labels for the AI
        labels = {
            "image": "final_form.pdf",
            "boxes": [{"class": "name_input", "bbox": bbox}]
        }

        with open("labels.json", "w") as f:
            json.dump(labels, f)

        print("Done. PDF created using Chrome engine.")
        print(f"Auto-detected Label Coordinates: {bbox}")

        browser.close()

if __name__ == "__main__":
    create_perfect_form()