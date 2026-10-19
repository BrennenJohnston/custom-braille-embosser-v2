# Makers Making Change documentation checklist

Where each of the seventeen items of the Open AT Template Guide's Final Documentation Checklist (V1.0.0, September 2024, pages 42 and 43) is met in this repository, and what is not met. The status words are: met, the item is satisfied by files here; owner, a step I still have to do; not met, the item cannot be satisfied and the reason is given; not applicable, the item is not about this device.

## The seventeen items

| Item | Status | Where, or why not |
|---|---|---|
| 1. At least one open source license applied | met | `LICENSES/`: CERN-OHL-W v2 (hardware), CC BY-SA 4.0 (documentation), GPL-3.0-or-later (scripts); named in `README.md` and `okh.yml` |
| 2. Alt text on every image in every document | met, review owner | Every picture in every page has alt text; `images.json` records each as draft until I have read it |
| 3. Device Summary completed | met | `Custom_Braille_Embosser_V2_Device_Summary.md` and `.pdf`; mass, print time and cost measured from the sliced X1C projects (section 6) |
| 4. PDF created for the User Guide | met | `Step_3_Guide_Custom_Braille_Embosser_V2_User_Guide.pdf`, printed from its Markdown by `scripts/build_assembly_guide_pdf.py` |
| 5. PDF created for the Maker Guide | met | `Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.pdf`; the Assembly Guide By Touch and the Visual Assembly Guide are its two further editions |
| 6. PDF created for the Design Workbook or Design Rationale | met, draft | `Custom_Braille_Embosser_V2_Design_Rationale.pdf` (the Rationale, not the Workbook) |
| 7. Bill of materials saved as a CSV file | met | `Custom_Braille_Embosser_V2_BOM.csv`; every mass and cost from the sliced X1C projects, each part sliced on its own |
| 8. All image files renamed, none left as a camera name | met | `tests/test_images_manifest.py` refuses any camera-style name under `Photos/` |
| 9. CAD design files added | not met | No CAD source exists for Version 2: the parts were exported as STL only. `Design_Files/README.md` says so |
| 10. STEP files added | not met | The same: no STEP export exists, and none can be made from the STL files without remodelling |
| 11. 3D printing files added | met | `Build_Files/3D_Printing_Files/STL/` (nine parts), the three X1C projects in `Print_Profiles/`, the tactile assembly map's plates, the example cylinder pair, the assembled reference |
| 12. Custom PCB design files (if required) | not applicable | No electronics |
| 13. Custom PCB build files (if required) | not applicable | No electronics |
| 14. GitHub repository created | owner | The repository exists locally with its history; I push it when this review round is done |
| 15. Unnecessary template folders and files removed | met | Only folders with content are kept; the working notes of the writing are kept outside the repository |
| 16. GitHub README complete | met, link owner | `README.md` follows the Open AT headings; the Makers Making Change project link is filled in when MMC assigns it |
| 17. Open Know-How manifest complete | met | `okh.yml` names every document, the printing files, the licenses and the lead picture |

## Beyond the checklist

These are not checklist items, but the template's guidance asks for them and the repository meets them.

- Document names follow `Custom_Braille_Embosser_V2_<Document>`; the seven guides carry the step they belong to in front, `Step_<N>_Guide_Option_<M>_`, so they sort in the order they are used.
- Pictures are between 500 by 350 and 1000 by 800 pixels in the pages, or larger files shown at that size; the lead picture is 1000 pixels wide.
- Every PDF is tagged, names its language, shows its title, has a bookmark for every heading, and carries each picture's alt text; `Documentation/README.md` says how that is checked and what a screen-reader check still has to confirm by hand.
- The print orientation of every part is in the sliced X1C projects.

## Where this list is kept up to date

Change this page when a document is added or an item's status changes; `README.md` links to it from its documentation table.
