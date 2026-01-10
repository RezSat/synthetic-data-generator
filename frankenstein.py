import random
import json
import os
from playwright.sync_api import sync_playwright

# 1. "Lorem Ipsum" for three Languages
# Just need blocks of text to create the visual "texture" of a paragraph.
TEXT_SI = "ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජයේ ආණ්ඩුක්‍රම ව්‍යවස්ථාව..."
TEXT_TA = "இலங்கை சனநாயக சோசலிசக் குடியரசின் அரசியலமைப்பு..."
TEXT_EN = "The Constitution of the Democratic Socialist Republic of Sri Lanka..."

def get_random_text():
    # Mix languages to simulate real government forms
    return random.choice([TEXT_SI, TEXT_TA, TEXT_EN]) * random.randint(1, 5)

# 2. The Atomic Layout Blocks (HTML)
# These are the "Lego blocks" the AI needs to learn to recognize.

def block_header():
    return f"""
    <div class="layout-box header" style="text-align: center; margin-bottom: 20px;">
        <h2 style="border: 1px solid red;">[HEADER: {get_random_text()[:20]}]</h2>
    </div>
    """

def block_key_value():
    # Simulates "Name: ................"
    return f"""
    <div class="layout-box input-row" style="display: flex; margin-bottom: 10px; align-items: flex-end;">
        <div style="width: 30%; font-weight: bold;">Label:</div>
        <div style="flex-grow: 1; border-bottom: 2px dotted black; height: 20px;"></div>
    </div>
    """

def block_table():
    # A random grid
    rows = ""
    for _ in range(random.randint(2, 5)):
        cols = ""
        for _ in range(3):
            cols += f'<td style="border: 1px solid black; padding: 5px;">Data</td>'
        rows += f"<tr>{cols}</tr>"
    
    return f"""
    <div class="layout-box table-container" style="margin-bottom: 20px;">
        <table style="width: 100%; border-collapse: collapse;">{rows}</table>
    </div>
    """

def block_paragraph():
    return f"""
    <div class="layout-box text-block" style="margin-bottom: 15px; text-align: justify;">
        {get_random_text()}
    </div>
    """

# 3. The Generator
def generate_layout_training_data(count=5):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        os.makedirs("layout_dataset", exist_ok=True)

        for i in range(count):
            # A. Compose a Random Page
            # Randomly stack blocks to create a unique document structure
            elements = [block_header, block_paragraph, block_key_value, block_table, block_key_value]
            random.shuffle(elements) # Randomize order

            html_body = "".join([e() for e in elements])
            
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&display=swap');
                    body {{ font-family: 'Noto Sans Sinhala', sans-serif; padding: 20mm; }}
                    /* "layout-box" class helps us find these elements later */
                    .layout-box {{ border: 1px dashed #ccc; padding: 5px; }} 
                </style>
            </head>
            <body>{html_body}</body>
            </html>
            """

            page.set_content(full_html)
            page.wait_for_load_state("networkidle")

            # B. Get Ground Truth Labels
            # Ask Chrome: "Where are the layout-boxes?"
            box_locators = page.locator(".layout-box").all()
            labels = []
            
            for idx, locator in enumerate(box_locators):
                # Determine class (Table vs Input) by checking the inner HTML or class list
                # For now, let's just get the coordinates
                bbox = locator.bounding_box()
                if bbox:
                    labels.append({
                        "id": idx,
                        "bbox": [bbox['x'], bbox['y'], bbox['width'], bbox['height']],
                        "type": "generic_layout_block" # refine this logic to say "table" or "header"
                    })

            # C. Save Data
            # 1. Image (The "Scan")
            page.screenshot(path=f"layout_dataset/train_{i}.jpg")
            
            # 2. JSON (The "Answer Key")
            with open(f"layout_dataset/train_{i}.json", "w") as f:
                json.dump({"boxes": labels}, f, indent=2)

            print(f"Generated layout_dataset/train_{i}.jpg")

        browser.close()

if __name__ == "__main__":
    generate_layout_training_data(count=1)