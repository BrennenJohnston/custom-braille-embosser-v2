# Documentation

The written guides for the Custom Braille Embosser, Version 2, and the files behind them.

## What is here

| File | What it is |
|---|---|
| `Step_1_Guide_Option_1_Custom_Braille_Embosser_V2_Web_Generator_Guide.md` and `.pdf` | Making the cylinders with the web generator, every step with a marked screenshot; pictures by `scripts/web_generator_screenshots.py`. |
| `Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md` and `.pdf` | The offline OpenSCAD file, from translating the text to exporting the STL; pictures by `scripts/openscad_gui_capture.py` and `scripts/openscad_guide_screenshots.py`. |
| `Step_2_Guide_Option_1_Custom_Braille_Embosser_V2_Visual_Assembly_Guide.md` and `.pdf` | The edition without words: a numbered panel a step, the part lifted away with a red dashed arrow to where it goes. |
| `Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md` and `.pdf` | The full edition: every step with a By touch block, every part described for the hands, for building without sight. |
| `Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.md` and `.pdf` | The short edition for whoever builds the embosser: print, twelve steps, test, troubleshoot; the cylinders are the Step 1 guides' subject. |
| `Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md` and `.pdf` | The key to the printed tactile assembly map: what each numbered shape is. Written by `scripts/tactile_assembly_map_key.py`. |
| `Step_3_Guide_Custom_Braille_Embosser_V2_User_Guide.md` and `.pdf` | For whoever embosses cards: how directions are given, embossing a card in seven steps, the rollers out for a new message, troubleshooting. |
| `Custom_Braille_Embosser_V2_BOM.csv` | The bill of materials, in the Makers Making Change layout. |
| `Custom_Braille_Embosser_V2_Device_Summary.md` and `.pdf` | What the device is, who it is for, what is in the kit, its sizes, what changed from Version 1, licenses. |
| `Custom_Braille_Embosser_V2_Design_Rationale.md` and `.pdf` | Why the parts are shaped as they are: keyed pegs, the barrel, the arrows, the seam channel, what was dropped. |
| `Custom_Braille_Embosser_V2_MakerWorld_Listing.md` and `.docx` | The MakerWorld listing, field by field, with the pictures to upload; `scripts/makerworld_listing_docx.py` makes the Word copy to paste from. |
| `Custom_Braille_Embosser_V2_Listing_Description.md` | The listing's description as plain Markdown for Thingiverse and Printables, whose fields strip pasted formatting; written by `scripts/listing_description_markdown.py`. |
| `parts.json` | The facts about each part: name, file, old engineering names, size in mm. The guide's parts table is written from it. |
| `images.json` | Every picture under `Photos/`: where it came from, what it shows, and whether its description has been reviewed. |

Each Markdown page is the source of every sentence and the screen-reader edition. The seven guides carry the step they belong to in front of their names (Step 1 makes the cylinders, Step 2 builds, Step 3 uses), so a folder of them sorts in the order they are read; the other documents keep the plain `Custom_Braille_Embosser_V2_` name.

## How the guides are written

The writing rules are stated once, in section 1 of the Assembly Guide By Touch; every guide follows them.

## Only what changes the outcome

Every sentence in a guide earns its place by one test: if it were removed and the reader never knew, would the reader be less able to finish the task, or less able to understand the directions? If the answer to both is no, the sentence goes. That removes what the pictures look like (the mat, the kit's colours, the screen), what I found or how long I take, links to other guides for their own sake, engineering file names, care and maintenance nobody has asked about, and troubleshooting rows for problems nobody has met. What stays is a part's shape and where its features are, a step, a check, a warning, and the fix for a problem that has happened. I set this rule on 2026-10-06; every new guide is written to it and every finished guide is read for it.

## No repeated information

A fact, rule or instruction is stated once in a document, where the reader needs it, and pointed to from anywhere else. Repeating it in other words is not allowed unless the repeat is intentional for impact or learning and was decided on purpose; the different editions of the assembly guide repeat each other by design, but no page repeats itself. Before a document is finished it is read once for this alone (my rule, 2026-10-06).

## Suggestions, not demands

The guides suggest and explain; they do not order. This project exists to give people options, not limits, and a reader may know more than I do. Where a reader has a choice (a setting, which generator, whether to print an optional part, the order of optional work), the page says what each option is for, may say which one I would start with and why, and leaves the choice with the reader. Nothing talks down to a reader: no telling them what they need not understand, what the usual way is, or what to leave alone. A procedure step stays a plain imperative (Hold, Lower, Press), because that is the shape of a step, and a safety warning stays a warning. My rule, 2026-10-06.

## How the PDF is built

`python scripts/build_assembly_guide_pdf.py --document all` turns each Markdown page into one HTML file and has headless Microsoft Edge or Google Chrome print it to PDF (`--document user-guide` prints one). The HTML stays in `build/assembly_guide_pdf/` for checking. The Visual Assembly Guide prints its parts panel on the cover and has no contents page; the User Guide prints its panel of four pictures under its title. The script then reads the PDF back and refuses to finish unless all of this holds:

- a heading, its words and the picture that follows stay on one page: the builder reads each print back, and where a picture fell onto the page after its heading it shrinks that page's pictures to the room under their words and prints again; only a step with too little room left moves whole (my layout rule, 2026-10-06);
- every page is US Letter;
- the PDF is tagged, names its language, and shows its title;
- there is a bookmark for every heading, in the heading order;
- every picture is a Figure with the alt text from the page, grouped with its caption;
- every table's column and row headers carry their scope;
- the contents page's numbers are the pages the sections land on;
- every link on the page is a link in the PDF.

The build writes a record a document (`scripts/assembly_guide_by_touch_pdf.json` and its siblings), the SHA-256 of the PDF and of every file it was printed from. `tests/test_assembly_guide_pdf.py` compares that record with the files as they are, so a change to the guide, a picture or the builder without a new print fails the tests.

`python scripts/pdf_structure_report.py Documentation/Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.pdf` prints the PDF's structure tree as text: the order a screen reader follows, with each figure's alt text and each table cell's scope.

## What a person still checks

The checks above are mechanical. Before a release, I read the PDF with a screen reader (NVDA on Windows) and confirm:

1. Press H through the headings: every section and every step is announced, in order, and nothing is skipped.
2. Press G to each graphic: the alt text is read, and the caption follows it.
3. Press T to a table: the column headers are announced as you move across a row.
4. Read one whole step from its heading to its By touch block: the Careful, Check and By touch paragraphs are read in place, as plain paragraphs.
5. Open the contents page and activate one entry: it lands on that section.

This repository makes no claim that the PDF meets PDF/UA, WCAG or any other standard. The checks say what was verified; nothing more.
