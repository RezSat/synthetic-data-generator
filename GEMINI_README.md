Gemini generated below so I won't go over the track once I sleep and wakeup again:

# Enterprise-Grade AI Document Reconstruction Pipeline (Sinhala/Tamil/English)

## 🚀 Project Overview
This project is not just an OCR system; it is a **Document Reconstruction Engine**. 
Unlike traditional OCR that outputs a stream of text, this pipeline understands the *structure* of government forms (tables, checkboxes, signatures, mixed-language fields) and reconstructs them into fully editable, pixel-perfect documents.

**Key Innovation:** We utilize a **Synthetic Data Factory** to train our Vision Models on millions of dynamically generated "Frankenstein" layouts, removing the need for manual labeling of thousands of real-world documents.

---

## 🏗 Architecture

The system follows a 4-stage "Neuro-Symbolic" pipeline:

### 1. The "Synthetic Factory" (Data Generation)
Instead of scraping real forms, we use a custom **Layout Engine** (`Playwright` + `Jinja2`) to generate 100,000+ unique document layouts.
* **Input:** Random text (Sinhala/Tamil/English) + Atomic Blocks (Header, Table, Input Field).
* **Process:** Renders HTML/CSS in a Headless Chrome browser.
* **Output:** * `image.png` (Training Input)
    * `labels.json` (Pixel-perfect Ground Truth Bounding Boxes)

### 2. The "Eyes" (Layout Analysis)
* **Model:** **LayoutLMv3** (Microsoft)
* **Task:** Object Detection & Layout Parsing.
* **Classes:** `text_block`, `table`, `key_value_pair`, `checkbox`, `signature_area`, `header`.
* **Why LayoutLMv3?** It understands that the visual position of text defines its meaning (e.g., text *under* a line is likely a form input).

### 3. The "Brain" (Multilingual OCR)
* **Strategy:** Region-based Routing.
* **Process:**
    1.  Crop the regions identified by LayoutLMv3.
    2.  Classify Script (Sinhala vs. English).
    3.  Route to specialized engines (Tesseract 5 / PaddleOCR with custom Indic fine-tuning).

### 4. The "Reconstruction" (Output Generation)
* **Engine:** **Playwright (Headless Chrome)**.
* **Logic:** The system does not edit the PDF. It writes fresh HTML/CSS code based on the detected layout and data, then "prints" a brand new PDF.
* **Benefit:** Solves the "Complex Text Shaping" issue (ligatures in Sinhala/Tamil) by leveraging the browser's native rendering engine.

---

## 🛠 Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | Core Logic |
| **Data Gen** | `Playwright`, `Jinja2` | Generating labeled synthetic datasets |
| **Training** | `PyTorch`, `HuggingFace` | Model training (Google Colab) |
| **Model** | **LayoutLMv3-Base** | Document Layout Analysis |
| **OCR** | `Tesseract`, `PaddleOCR` | Text Extraction |
| **Frontend** | React / Next.js (Planned) | Human-in-the-loop correction UI |

---

## ⚡ Quick Start: Generating Data

We do not label data manually. We generate it.

1.  **Install Dependencies:**
    ```bash
    pip install playwright jinja2 faker
    playwright install chromium
    ```

2.  **Run the Factory:**
    ```bash
    python frankensteinv2.py --count 1000 --out_dir dataset_complex
    ```
    * Generates 1,000 unique layouts.
    * Saves images to `dataset_complex/images/`.
    * Saves auto-labeled annotations to `dataset_complex/labels/`.

---

## 🧠 Model Training (Colab Roadmap)

Since we are using **LayoutLMv3**, training requires GPU acceleration.
* **Notebook:** `training/train_layoutlmv3.ipynb`
* **Platform:** Google Colab (Free T4 GPU is sufficient for base models).
* **Dataset Format:** COCO Format (JSON) or HuggingFace Dataset format.

---

## 🔮 Future Roadmap
* [ ] **Post-Training:** Fine-tune on a small set (50-100) of *real* scanned K-Forms to adapt to scanner noise.
* [ ] **Signature Verification:** Add a classification head to detect if a signature box is empty or signed.
* [ ] **Web UI:** Build a split-screen interface for verifying OCR results.