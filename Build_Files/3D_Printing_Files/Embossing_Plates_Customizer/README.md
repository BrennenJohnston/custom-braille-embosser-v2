# Embossing Plates Customizer: make your own cylinders

The embosser does not carry any braille itself. The message is on a pair of cylinders, Cylinder A with the raised dots and Cylinder B with the matching dimples, generated for your text and printed. This folder is how you make that pair. The companion folder [`Embossing_Plates_Examples/`](../Embossing_Plates_Examples) holds a ready-made pair that says "Washington", for a first test print before you generate your own.

## Two ways to make the pair

Each way has its own step-by-step guide with pictures, from the first click to the printed pair: the [Web Generator Guide](../../../Documentation/Step_1_Guide_Option_1_Custom_Braille_Embosser_V2_Web_Generator_Guide.md) and the [OpenSCAD Generator Guide](../../../Documentation/Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md).

### 1. The web app

<https://braille-cylinder-stl-generator.vercel.app>: it translates your text to braille (Liblouis, more than fifty language tables), shows the pair in 3D before you download, works with a screen reader, and runs entirely in your browser, so your text never leaves your computer. Source: <https://github.com/BrennenJohnston/braille-cylinder-stl-generator> (PolyForm Noncommercial 1.0.0).

### 2. OpenSCAD, offline

A verbatim copy of the Version 2 generator is in [`OpenSCAD_Offline_Alternative/`](OpenSCAD_Offline_Alternative), for OpenSCAD 2021.01 or newer; its [README](OpenSCAD_Offline_Alternative/README.md) lists the files and where they come from. It takes your text already in Unicode braille. The same generator runs on MakerWorld as a customizer inside the embosser's listing, from the standard-cylinder file in [`MakerWorld_Customizer/`](MakerWorld_Customizer); the second file there, with the gears fixed on, is kept for an upload of your own.

License of the generator: PolyForm Noncommercial 1.0.0, in [`OpenSCAD_Offline_Alternative/LICENSE_PolyForm_Noncommercial_1.0.0.md`](OpenSCAD_Offline_Alternative/LICENSE_PolyForm_Noncommercial_1.0.0.md). The copy is release v2.12.0 (commit `705fe9a`, 2026-10-09) of [`braille-cylinder-stl-generator-openscad`](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad); `VENDORED.json` beside it records the hashes.

## Choosing between them

| If you | Then |
|---|---|
| want nothing to install, or do not have OpenSCAD | the web app |
| want your text translated for you | the web app |
| use a screen reader | the web app, or the OpenSCAD copy through [`openscad-assistive-forge`](https://github.com/BrennenJohnston/openscad-assistive-forge) |
| need to work with no internet | OpenSCAD |
| want every dot and spacing dimension as a dial, or want to read or change the code | OpenSCAD |
| want to make many pairs from a script | OpenSCAD (`openscad -D ... -o out.stl`) |

Both make the same cylinders: 30.8 mm across, 54 mm tall, with the keyed holes that take the four gears.

## The card thickness setting

Both generators make the pair for 0.4 mm card (about 150 lb, 350 gsm), which is most business cards, and that is the setting to leave alone. The 0.3 mm setting (about 110 to 130 lb, 250 to 300 gsm card) is for when a 0.4 mm pair punches holes through the card instead of leaving rounded dots; it sits under Expert Mode in the web app and in the Expert Mode - Card Thickness group of the OpenSCAD file. Both cylinders of a pair are made at one setting and go in together.

## One-piece rollers

Both generators can also make the cylinders with the four gears already part of them: the web app's Simplified gears (Web Generator Guide, section 13) and the OpenSCAD file's Gears tab (OpenSCAD Generator Guide, section 4).
