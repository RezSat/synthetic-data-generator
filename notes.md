I tried to use reportlab to create these documents, but as it turns out report lab sucks at rendering sinhala text.

so there were few suggestions i found which is to use harfbuzz or pillow, both failed and gives similar results to above or sometimes even worse (using harfbuzz)

so completely ditch them and instead I tried to write a custom rendering engine (hehehe). But then it clicked me, the perfect rendering engine already exists and it just sit in my machine right here. Chrome? google has spend millions to make the perfect text rendering engine for various languages including sinhala.

Therefore next step is to levarage that.

Playwright method is the best as it runs on the chromium engine (or chrome) and is the arguably the best rendering engine available.

so we building the document using html, css and use jinja to create templates.