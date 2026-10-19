# OpenSCAD offline alternative: the Version 2 cylinder generator

This is the offline copy of the generator. The web app at <https://braille-cylinder-stl-generator.vercel.app> translates your text and runs in the browser; this copy runs offline, gives every dimension as a dial, and can be read and changed. The [parent README](../README.md) compares the two.

The folder is a verbatim copy of the Embosser Version 2 generator from [`braille-cylinder-stl-generator-openscad`](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad), vendored so the embosser project is usable with no internet connection. For the latest version, fixes and the full test suite, go to the upstream repository.

| Field | Value |
|---|---|
| Vendored from | [`BrennenJohnston/braille-cylinder-stl-generator-openscad`](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad) |
| Upstream version | release v2.12.0, commit `705fe9a` (2026-10-09), copied 2026-10-19; hashes in `VENDORED.json` |
| License | [PolyForm Noncommercial 1.0.0](LICENSE_PolyForm_Noncommercial_1.0.0.md) |
| Maintainer | Brennen Johnston |
| Software | [OpenSCAD](https://openscad.org/) 2021.01 or newer; the 2026 development snapshot is faster |

License note: the embosser itself is CERN-OHL-W v2 (hardware), CC BY-SA 4.0 (documentation) and GPL-3.0-or-later (software). This generator is a separately licensed component under PolyForm Noncommercial 1.0.0: free for personal, educational and other non-commercial use, modification allowed, no commercial use. The web app carries the same license.

## Files

| File | What it is |
|---|---|
| `Braille_Cylinder_STL_Generator_EmbosserV2.scad` | The generator. Open this in OpenSCAD. It is self-contained apart from the two gear files below. |
| `assets/v2_gears_a.stl`, `assets/v2_gears_b.stl` | The Version 2 gears, used only by the Gears tab (one-piece rollers). Never edit them; `assets/GEARS_PROVENANCE.json` says where they come from. |
| `CHANGELOG.md` | The upstream changelog at the time of copying. |
| `LICENSE_PolyForm_Noncommercial_1.0.0.md` | The generator's license. |
| `VENDORED.json` | The upstream commit and the SHA-256 of every copied file. |

## Using it

The [OpenSCAD Generator Guide](../../../../Documentation/Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md) takes you from translating your text to the exported STL, with a picture of every step.

## Checking a render from the command line

```
openscad --hardwarnings --check-parameter-ranges=true -o pair.stl Braille_Cylinder_STL_Generator_EmbosserV2.scad
```

A clean run prints no line beginning `WARNING:` or `ERROR:` and writes `pair.stl`. The project checked this copy that way when it was vendored.
