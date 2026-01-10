I tried to use reportlab to create these documents, but as it turns out report lab sucks at rendering sinhala text.

so there were few suggestions i found which is to use harfbuzz or pillow, both failed and gives similar results to above or sometimes even worse (using harfbuzz)

so completely ditch them and instead I tried to write a custom rendering engine (hehehe). But then it clicked me, the perfect rendering engine already exists and it just sit in my machine right here. Chrome? google has spend millions to make the perfect text rendering engine for various languages including sinhala.

Therefore next step is to levarage that.

Playwright method is the best as it runs on the chromium engine (or chrome) and is the arguably the best rendering engine available.

so we building the document using html, css and use jinja to create templates.

But on the second thought, creating templates is not going to work because then the model/system will fail on completely different layout. Instead a better way to do this is using atomic elements.

so the new idea is Data Generator should be randomized.
We manuallly declare atomic blocks then start with a blank A4 sheet add different parts by randonmizing so we have many variations for the dataset.

text_block -> <p>
key_value_pair -> <div class="field"> ex: "Name: ................"

The Logic:
    Start Page: Blank A4.
    Roll Dice (Row 1): Result = "Header".  Draw centered bold text.
    Roll Dice (Row 2): Result = "Two Column Text".  Draw two paragraphs side-by-side.
    Roll Dice (Row 3): Result = "Table".  Draw a random table with 3 rows and 4 columns.
    Roll Dice (Row 4): Result = "Checklist".  Draw 5 lines of text with squares on the right

Gemini help me refine the script "frankenstein.py" which generated the dataset_v1, using the predefined blocks and randomizing the placement of these blocks on an A4 sized imge. By adding more block types and using different filling areas on the paper we could generate an enormous amount of dataset.

so started by thinking of using LayoutLMv3 but turns out our dataset is the wrong dataset for it and therefore now we are usimng YOLO instead of that.

Alright generated 1000 with frakensteinv2 and then train the model with YOLO and it gives pretty decent results.

next step is OCR