<!--- Open Source Assistive Technology: GitHub Readme based on OpenAT-Template v1.2 (2025-Feb-04). Original template: https://github.com/makersmakingchange/OpenAT-Template --->

# Custom Braille Embosser, Version 2

## Overview
The Custom Braille Embosser, Version 2 is an open-source assistive technology device that lets a blind or low-vision user, or a sighted helper, hand-emboss permanent raised braille onto business-card stock. The braille message lives on a pair of interchangeable cylinders that are generated from text, so changing the message means printing a new pair.

I started this project because I couldn't find a quick and affordable way to make custom braille business cards: the tools that exist are a slate and stylus, a Perkins-style brailler, or an electronic embosser that costs more than most people will spend on a few cards. Version 1 fixed that for me. Many of the people who printed it were kind enough to tell me what needed to change to make it more accessible, and Version 2 is the result of their feedback.

Version 2 is made of nine 3D-printed parts plus the two generated cylinders. There are no off-the-shelf electronics, no fasteners, no springs and no glue: every part snaps or slides together by hand. Each of the four gears has a differently shaped peg, and each cylinder end has a matching keyed hole, so a gear only fits where it belongs.

The device is open assistive technology (OpenAT). Under the open-source licenses in this repository it may be built, used and improved upon by anyone.

The cost of materials is a few US dollars of 3D-printer filament per device, plus card stock and the filament for the cylinders.

## Makers Making Change Assistive Device Library
<MMCWebLink>

> The MMC library URL is assigned by Makers Making Change after submission, so this placeholder stays until then. The embosser is also listed on [MakerWorld](https://makerworld.com/en/models/3405044-custom-braille-card-embosser-v2-tactile-friendly) and [Thingiverse](https://www.thingiverse.com/thing:7419301).

## How to Obtain the Device
### 1. Do-it-Yourself (DIY) or Do-it-Together (DIT)

This is an open-source assistive technology, so anyone is free to build it. All of the files and instructions required to build the device are in this repository.

### 2. Request a build of this device

You may also submit a build request through the [Makers Making Change Assistive Device Library Listing](<MMCWebLink>) to have a volunteer maker build the device. As the requestor, you are responsible for reimbursing the maker for the cost of materials and any shipping.

### 3. Build this device for someone else

If you have the skills and equipment to build this device, and would like to donate your time to create the device for someone who needs it, visit the [MMC Maker Wanted](https://makersmakingchange.com/maker-wanted/) section.

## Generating the Braille Cylinders
Cylinder A and Cylinder B roll against each other with the card between them. You tell them apart by the column of arrows down each one's side: Cylinder A's arrows stand up from the surface and Cylinder B's are sunk into it. (With a single-sided card, A carries the raised dots and B the matching dimples; with the double-sided option, both carry dots and dimples, so the arrows are the sure sign.) Both are generated for your text, in the browser at <https://braille-cylinder-stl-generator.vercel.app> (type the text, choose Version 2 under Embosser setup, and download both files) or with the OpenSCAD file in [`Build_Files/3D_Printing_Files/Embossing_Plates_Customizer`](/Build_Files/3D_Printing_Files/Embossing_Plates_Customizer). Nothing you type leaves your browser.

The cylinders for Version 2 are 30.8 mm across and 54 mm tall; cylinders made for Version 1 do not fit.

## Build Instructions
### 1. Print the 3D-printable parts

The part files are in [`Build_Files/3D_Printing_Files/STL`](/Build_Files/3D_Printing_Files/STL). Sliced Bambu Lab X1C projects, the nine parts on one plate, the example cylinder pair and the tactile assembly map, are in [`Build_Files/3D_Printing_Files/Print_Profiles`](/Build_Files/3D_Printing_Files/Print_Profiles).

### 2. Generate and print the cylinders

Follow [Generating the Braille Cylinders](#generating-the-braille-cylinders) above. Cylinder A and Cylinder B are made together as a pair and go in together.

### 3. Assemble the device

The [Maker Guide](/Documentation/Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.md) walks through the build in a few pages. The [Assembly Guide By Touch](/Documentation/Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md) says every step for the hands, so the embosser can be built without sight, and the [Visual Assembly Guide](/Documentation/Step_2_Guide_Option_1_Custom_Braille_Embosser_V2_Visual_Assembly_Guide.md) shows it without words. Each is also printed as a tagged PDF.

## How to Improve this Device
As open-source assistive technology, you are welcome and encouraged to improve on the design. If you build one, tell me what confused you, in an issue here or a comment on the listing: that is the most useful thing I can hear.

## Files
### Documentation
| Document | Version | Link |
|---|---|---|
| Step 1, option 1: Web generator guide | 2.0 | [Markdown](/Documentation/Step_1_Guide_Option_1_Custom_Braille_Embosser_V2_Web_Generator_Guide.md), [PDF](/Documentation/Step_1_Guide_Option_1_Custom_Braille_Embosser_V2_Web_Generator_Guide.pdf): making the cylinders with the web app, step by step with pictures |
| Step 1, option 2: OpenSCAD generator guide | 2.0 | [Markdown](/Documentation/Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md), [PDF](/Documentation/Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.pdf): the offline file and the MakerWorld customizer, with a translator for the braille |
| Step 2, option 1: Visual assembly guide | 2.0 | [Markdown](/Documentation/Step_2_Guide_Option_1_Custom_Braille_Embosser_V2_Visual_Assembly_Guide.md), [PDF](/Documentation/Step_2_Guide_Option_1_Custom_Braille_Embosser_V2_Visual_Assembly_Guide.pdf) |
| Step 2, option 2: Assembly guide by touch | 2.0 | [Markdown](/Documentation/Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md), [PDF](/Documentation/Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.pdf) |
| Step 2, option 3: Maker guide | 2.0 | [Markdown](/Documentation/Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.md), [PDF](/Documentation/Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.pdf) |
| Step 2, option 4: Tactile assembly map key | 2.0 | [Markdown](/Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md), [PDF](/Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.pdf) |
| Step 3: User guide | 2.0 | [Markdown](/Documentation/Step_3_Guide_Custom_Braille_Embosser_V2_User_Guide.md), [PDF](/Documentation/Step_3_Guide_Custom_Braille_Embosser_V2_User_Guide.pdf) |
| Bill of materials | 2.0 | [CSV](/Documentation/Custom_Braille_Embosser_V2_BOM.csv) |
| Device summary | 2.0 | [Markdown](/Documentation/Custom_Braille_Embosser_V2_Device_Summary.md), [PDF](/Documentation/Custom_Braille_Embosser_V2_Device_Summary.pdf) |
| Design rationale | 2.0 | [Markdown](/Documentation/Custom_Braille_Embosser_V2_Design_Rationale.md), [PDF](/Documentation/Custom_Braille_Embosser_V2_Design_Rationale.pdf) |
| Documentation checklist | 2.0 | [Markdown](/Documentation/COMPLIANCE_CHECKLIST.md): the seventeen Makers Making Change items and where each is met |
| MakerWorld listing | 2.0 | [Markdown](/Documentation/Custom_Braille_Embosser_V2_MakerWorld_Listing.md), [Word](/Documentation/Custom_Braille_Embosser_V2_MakerWorld_Listing.docx): the listing field by field with its pictures; a [plain description](/Documentation/Custom_Braille_Embosser_V2_Listing_Description.md) for Thingiverse and Printables |
| Change log | 2.0 | [CHANGES.txt](CHANGES.txt) |

How the documents are written and checked is in [`Documentation/README.md`](/Documentation/README.md).

### Design Files
Version 2 is published as STL files only; see [`Design_Files`](/Design_Files).

### Build Files
- [3D printing files: STL, the sliced X1C projects, the tactile assembly map](/Build_Files/3D_Printing_Files)

### Video Tutorials
A rendered animation of the whole assembly, and one clip a step, are in [`Video_Tutorials`](/Video_Tutorials); a filmed tutorial follows when I have edited it.

## License
Copyright (c) 2026 Brennen Johnston.

This repository describes Open Hardware:
- Everything needed or used to design, make, test, or prepare the Custom Braille Embosser, Version 2 is licensed under the [CERN 2.0 Weakly Reciprocal license (CERN-OHL-W v2) or later](https://cern.ch/cern-ohl).
- All software, including the scripts in `scripts/` and `tests/`, is under the [GNU General Public License v3.0 or later (GPL-3.0-or-later)](https://www.gnu.org/licenses/gpl.html).
- Accompanying material such as the guides, photographs and videos is published under a [Creative Commons Attribution-ShareAlike 4.0 license (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).

The web-based cylinder generator at <https://braille-cylinder-stl-generator.vercel.app> is a separate project under its own license (PolyForm Noncommercial 1.0.0). The OpenSCAD generator files copied into [`Build_Files/3D_Printing_Files/Embossing_Plates_Customizer/`](/Build_Files/3D_Printing_Files/Embossing_Plates_Customizer) come from [braille-cylinder-stl-generator-openscad](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad) and are under PolyForm Noncommercial 1.0.0 as well, in [`LICENSE_PolyForm_Noncommercial_1.0.0.md`](/Build_Files/3D_Printing_Files/Embossing_Plates_Customizer/OpenSCAD_Offline_Alternative/LICENSE_PolyForm_Noncommercial_1.0.0.md).

You may redistribute and modify this documentation and make products using it under the terms of the [CERN-OHL-W v2](https://cern.ch/cern-ohl).
This documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
Please see the CERN-OHL-W v2 for applicable conditions.

Source Location: https://github.com/BrennenJohnston/custom-braille-embosser-v2

## Attribution
The device was designed by Brennen Johnston. Version 1 is published at [custom-braille-embosser-3d-printing-project](https://github.com/BrennenJohnston/custom-braille-embosser-3d-printing-project).

The cylinder generators are the companion projects [braille-cylinder-stl-generator](https://github.com/BrennenJohnston/braille-cylinder-stl-generator) (web-based) and [braille-cylinder-stl-generator-openscad](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad) (OpenSCAD), also by Brennen Johnston. The braille translation in the web app is powered by the open-source [Liblouis](https://liblouis.io/) library.

The documentation template was created by Makers Making Change / Neil Squire Society and is used under a CC BY-SA 4.0 license. It is available at: [https://github.com/makersmakingchange/OpenAT-Template](https://github.com/makersmakingchange/OpenAT-Template)

### Contributors
Designers:
- Brennen Johnston

Testers:
- Brennen Johnston

---
<!-- ABOUT MMC START -->
## About Makers Making Change
[<img src="https://raw.githubusercontent.com/makersmakingchange/makersmakingchange/main/img/mmc_logo.svg" width="500" alt="Makers Making Change Logo">](https://www.makersmakingchange.com/)

Makers Making Change is a program of [Neil Squire](https://www.neilsquire.ca/), a Canadian non-profit that uses technology, knowledge, and passion to empower people with disabilities.

Makers Making Change leverages the capacity of community based Makers, Disability Professionals and Volunteers to develop and deliver affordable Open Source Assistive Technologies.

 - Website: [www.MakersMakingChange.com](https://www.makersmakingchange.com/)
 - GitHub: [makersmakingchange](https://github.com/makersmakingchange)
 - Bluesky: [@makersmakingchange.bsky.social](https://bsky.app/profile/makersmakingchange.bsky.social)
 - Instagram: [@makersmakingchange](https://www.instagram.com/makersmakingchange)
 - Facebook: [makersmakechange](https://www.facebook.com/makersmakechange)
 - LinkedIn: [Neil Squire Society](https://www.linkedin.com/company/neil-squire-society/)
 - Thingiverse: [makersmakingchange](https://www.thingiverse.com/makersmakingchange/about)
 - Printables: [MakersMakingChange](https://www.printables.com/@MakersMakingChange)

### Contact Us
For technical questions, to get involved, or to share your experience we encourage you to [visit our website](https://www.makersmakingchange.com/) or [contact us](https://www.makersmakingchange.com/s/contact).
<!-- ABOUT MMC END -->
