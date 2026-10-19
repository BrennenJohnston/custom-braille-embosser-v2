// Custom Braille Embosser, Version 2: the tactile assembly map.
//
// Flat plates that carry the outline of every mating face of the embosser,
// true to size, as a map you read by touch before you build: each keyhole,
// peg, bump, dent, notch and stud, drawn as seen from above the assembled
// embosser, so a peg's shape lies exactly over the hole it enters. Every
// shape rises from the plate in equal steps (level_step_mm): its first level
// stands two steps up, each thing on that face one step more, at most four
// steps a shape; a sunk feature is one step lower than the face around it.
// Each shape has a raised numeral beside it and the same count cut as
// notches in the plate's near edge; with braille labels on, its number in
// braille stands above it on a sloped face that looks toward you, joined to
// the shape by a raised line one step tall. The key document says what each
// number is:
// Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md
//
// The outlines come from the part files themselves, cut by
// scripts/derive_tactile_assembly_map.py into tactile_assembly_map_shapes.scad beside this
// file. Never edit that file; rerun the script. The single-file copy for
// MakerWorld beside this file is written from the two by
// scripts/tactile_assembly_map_makerworld.py: rerun it after any change here.
//
// Printing: 0.2 mm layers (0.1 mm over the braille reads smoother), any
// rigid filament, no supports, the plate flat on the bed. The numerals and
// notches face you when the plate's long edge with the notches is nearest
// you; the braille faces you too.
//
// License: CERN-OHL-W v2 (the embosser's hardware license).

include <tactile_assembly_map_shapes.scad>

/* [Which plate] */
// 0 shows every plate side by side (preview only); 1 to 6 export one plate
plate = 0; // [0:All plates (preview), 1:Plate 1 - Roller A, 2:Plate 2 - Roller B, 3:Plate 3 - Knob and Lid, 4:Plate 4 - Handle, 5:Plate 5 - Base from above, 6:Plate 6 - Base from below]

/* [Plate] */
// Plate thickness in mm; 1.2 mm is the thinnest that prints well
plate_thickness_mm = 1.2; // [1.2:0.1:2.0]
// Height of one step between levels, mm; 0.5 mm is the least a finger finds, 1 mm the guidelines' recommended height
level_step_mm = 0.75; // [0.5:0.25:1.0]
// Room between two shapes, mm (at least 5 mm so separate features read apart)
shape_gap_mm = 10; // [6:1:16]
// Room between a shape and the plate's edge, mm
plate_margin_mm = 7; // [5:1:12]
// Corner radius of the plate, mm
plate_corner_mm = 3;

/* [Labels] */
// Height of the raised numerals above the plate, mm; 1.0 mm is the standard
numeral_height_mm = 1.0; // [0.5:0.5:1.5]
// Numeral size (cap height), mm
numeral_size_mm = 10; // [8:1:14]
// Edge notch width, depth and pitch, mm
notch_width_mm = 2.0;
notch_depth_mm = 1.5;
notch_pitch_mm = 3.5;

/* [Braille labels] */
// Each shape's number in braille on a sloped face above it, facing you; off for a reader who does not read braille
braille_labels = true;
// Room between a shape's top and the foot of its braille block, mm: a finger's width, so a hand reading the block does not land on the shape (the guidelines' 3 to 6 mm is for flat labels)
label_gap_mm = 15; // [3:1:30]
// Sloped face below the braille, mm: lifts the cells so a fingertip reading them rests on the block, not on the plate
braille_foot_mm = 12; // [2:1:20]
// Width of the raised line from a braille label down to its shape, mm
trace_width_mm = 1.2; // [1:0.1:2]
// How much wider the line's foot is than the line, each side, mm; 0 is straight sides
trace_flare_mm = 0.5; // [0:0.1:1]

/* [Hidden] */
// The shapes file writes each level's height in units of TACTILE_STEP_MM; the map scales them by level_step_mm.
step_mm = TACTILE_STEP_MM;
shape_lift_mm = level_step_mm;         // every shape's first level stands one step above the trace lines
trace_height_mm = level_step_mm;       // a trace line is one step tall: a full step below any shape
numeral_font = "Liberation Sans:style=Bold";
label_band_mm = numeral_size_mm + 6;   // room under each shape for its numeral
preview_gap_mm = 10;                   // room between two plates in the all-plates preview
$fn = 48;

// The braille label is a solid wedge: its face leans back at the angle
// readers found fastest and most comfortable for printed braille (Puerta et
// al., CHI 2024), its back is a ramp, so it prints flat with no supports.
face_angle_deg = 75;
back_angle_deg = 60;
wedge_top_mm = 1.5;                    // the flat along the wedge's top
// Dots and cells inside the ADA 703.3 / BANA ranges: base 1.5 to 1.6, height
// 0.6 to 0.9, dot pitch 2.3 to 2.5, cell pitch 6.1 to 7.6 mm. A frustum
// under a spherical cap, as the braille sign and the cylinder generator use.
dot_base_mm = 1.5;
dot_dome_mm = 1.0;
dot_base_height_mm = 0.3;
dot_dome_height_mm = 0.5;
dot_pitch_mm = 2.5;
cell_pitch_mm = 6.5;
dot_sink_mm = 0.05;                    // a dot's base sits this far inside the face
face_margin_x_mm = 2.5;                // room beside the cells on the face
face_margin_top_mm = 2.0;              // room above them; the room below is the braille_foot_mm dial
trace_slice_mm = 0.1;                  // the trace line's profile is stacked from slices this tall
// Braille digits as dot numbers (1 to 3 the left column from the top, 4 to
// 6 the right); the numeric indicator stands before the digits.
number_sign = [3, 4, 5, 6];
digit_dots = [[2, 4, 5], [1], [1, 2], [1, 4], [1, 4, 5], [1, 5], [1, 2, 4], [1, 2, 4, 5], [1, 2, 5], [2, 4]];

cell_w_mm = dot_pitch_mm + dot_base_mm;
cell_h_mm = 2 * dot_pitch_mm + dot_base_mm;
face_h_mm = braille_foot_mm + cell_h_mm + face_margin_top_mm;
cells_up_mm = braille_foot_mm + cell_h_mm / 2;   // the cells' centre, measured up the face from its foot
wedge_h_mm = face_h_mm * sin(face_angle_deg);
face_run_mm = face_h_mm * cos(face_angle_deg);
back_run_mm = wedge_h_mm / tan(back_angle_deg);
wedge_depth_mm = face_run_mm + wedge_top_mm + back_run_mm;
braille_band_mm = braille_labels ? label_gap_mm + wedge_depth_mm : 0;   // room above each shape for its label

// The plates: which faces (by number) sit on each, one row left to right in
// step order. Every plate fits a 200 x 200 mm bed.
plates = [
    [[1, 2, 3, 4]],      // Plate 1: Roller A - Cylinder A top, Top Gear A, Cylinder A bottom, Bottom Gear A
    [[5, 6, 7, 8]],      // Plate 2: Roller B
    [[9, 10]],           // Plate 3: Knob and Lid
    [[11]],              // Plate 4: Handle
    [[12]],              // Plate 5: Base from above
    [[13]],              // Plate 6: Base from below
];
plate_names = ["Roller A", "Roller B", "Knob and Lid", "Handle", "Base from above", "Base from below"];

// The dial ranges above, enforced: a value outside them fails the headless
// check instead of making a plate that was never tested. The notch dials
// have no documented range and so no guard.
assert(plate == floor(plate) && plate >= 0 && plate <= len(plates), "plate must be 0 (every plate) or 1 to 6");
assert(plate_thickness_mm >= 1.2 && plate_thickness_mm <= 2.0, "plate_thickness_mm must be 1.2 to 2.0");
assert(level_step_mm >= 0.5 && level_step_mm <= 1.0, "level_step_mm must be 0.5 to 1.0");
assert(shape_gap_mm >= 6 && shape_gap_mm <= 16, "shape_gap_mm must be 6 to 16");
assert(plate_margin_mm >= 5 && plate_margin_mm <= 12, "plate_margin_mm must be 5 to 12");
assert(numeral_height_mm >= 0.5 && numeral_height_mm <= 1.5, "numeral_height_mm must be 0.5 to 1.5");
assert(numeral_size_mm >= 8 && numeral_size_mm <= 14, "numeral_size_mm must be 8 to 14");
assert(label_gap_mm >= 3 && label_gap_mm <= 30, "label_gap_mm must be 3 to 30");
assert(braille_foot_mm >= 2 && braille_foot_mm <= 20, "braille_foot_mm must be 2 to 20");
assert(trace_width_mm >= 1 && trace_width_mm <= 2, "trace_width_mm must be 1 to 2");
assert(trace_flare_mm >= 0 && trace_flare_mm <= 1, "trace_flare_mm must be 0 to 1");
// The braille geometry against its spec (ADA 703.3.1), should anyone edit the constants.
assert(dot_base_mm >= 1.5 && dot_base_mm <= 1.6, "dot_base_mm must be 1.5 to 1.6");
assert(dot_base_height_mm + dot_dome_height_mm >= 0.6 && dot_base_height_mm + dot_dome_height_mm <= 0.9, "dot height must be 0.6 to 0.9");
assert(dot_pitch_mm >= 2.3 && dot_pitch_mm <= 2.5, "dot_pitch_mm must be 2.3 to 2.5");
assert(cell_pitch_mm >= 6.1 && cell_pitch_mm <= 7.6, "cell_pitch_mm must be 6.1 to 7.6");

function face(n) = tactile_faces[n - 1];
function face_w(n) = face(n)[2][0];
function face_h(n) = face(n)[2][1];
function face_levels(n) = len(face(n)[4]);
function row_width(fs, i = 0) = i >= len(fs) ? -shape_gap_mm : face_w(fs[i]) + shape_gap_mm + row_width(fs, i + 1);
function row_height(fs, i = 0) = i >= len(fs) ? 0 : max(face_h(fs[i]), row_height(fs, i + 1));
function row_levels(fs, i = 0) = i >= len(fs) ? 0 : max(face_levels(fs[i]), row_levels(fs, i + 1));
function row_band(fs) = row_height(fs) + label_band_mm + braille_band_mm;
function rows_width(rows, i = 0) = i >= len(rows) ? 0 : max(row_width(rows[i]), rows_width(rows, i + 1));
function rows_levels(rows, i = 0) = i >= len(rows) ? 0 : max(row_levels(rows[i]), rows_levels(rows, i + 1));
// The height taken by the rows below row r (each with the gap above it).
function below(rows, r) = r + 1 >= len(rows) ? 0 : row_band(rows[r + 1]) + shape_gap_mm + below(rows, r + 1);
function plate_w(rows) = rows_width(rows) + 2 * plate_margin_mm;
function plate_h(rows) = below(rows, -1) - shape_gap_mm + 2 * plate_margin_mm;
// The plate's highest point: its deepest shape, or a braille wedge when the labels are on.
function plate_top(rows) = plate_thickness_mm + max(shape_lift_mm + rows_levels(rows) * level_step_mm, braille_labels ? wedge_h_mm : 0);
function face_x(fs, k, i = 0) = i >= k ? 0 : face_w(fs[i]) + shape_gap_mm + face_x(fs, k, i + 1);
// The y of a row's label baseline: rows are counted from the top, and the last row sits on the notched edge.
function row_y(rows, r) = plate_margin_mm + below(rows, r);

module rounded_plate(w, h, t) {
    hull() for (x = [plate_corner_mm, w - plate_corner_mm], y = [plate_corner_mm, h - plate_corner_mm])
        translate([x, y, 0]) cylinder(r = plate_corner_mm, h = t);
}

// One face's shape: every level extruded from the plate to its own height.
module face_shape(n) {
    f = face(n);
    translate(f[3]) for (lvl = f[4])
        linear_extrude(height = plate_thickness_mm + shape_lift_mm + (lvl[0] / step_mm) * level_step_mm)
            for (pg = lvl[1]) polygon(points = pg[0], paths = pg[1]);
}

module numeral(n) {
    linear_extrude(height = plate_thickness_mm + numeral_height_mm)
        text(str(n), size = numeral_size_mm, font = numeral_font, halign = "center", valign = "baseline");
}

module edge_notches(n, x_centre) {
    span = (n - 1) * notch_pitch_mm;
    for (i = [0 : n - 1])
        translate([x_centre - span / 2 + i * notch_pitch_mm - notch_width_mm / 2, -0.01, -0.01])
            cube([notch_width_mm, notch_depth_mm + 0.01, plate_thickness_mm + 10]);
}

// A number's braille cells as lists of dot numbers: the numeric indicator, then a cell a digit.
function digits(n) = n < 10 ? [n] : concat(digits(floor(n / 10)), [n % 10]);
function cells(n) = concat([number_sign], [for (d = digits(n)) digit_dots[d]]);
function label_w(cs) = (len(cs) - 1) * cell_pitch_mm + cell_w_mm + 2 * face_margin_x_mm;

// One dot, base at z = 0: a frustum under a spherical cap of radius R = (r^2 + h^2) / 2h.
module braille_dot() {
    R = (pow(dot_dome_mm / 2, 2) + pow(dot_dome_height_mm, 2)) / (2 * dot_dome_height_mm);
    cylinder(h = dot_base_height_mm + 0.01, r1 = dot_base_mm / 2, r2 = dot_dome_mm / 2);
    intersection() {
        translate([0, 0, dot_base_height_mm + dot_dome_height_mm - R]) sphere(r = R);
        translate([-R, -R, dot_base_height_mm]) cube([2 * R, 2 * R, dot_dome_height_mm + 0.01]);
    }
}

// The cells laid flat about the origin, dots up, reading along +x, the first row of dots at +y.
module braille_cells(cs) {
    x0 = -(len(cs) - 1) * cell_pitch_mm / 2;
    for (i = [0 : len(cs) - 1], k = cs[i])
        translate([x0 + i * cell_pitch_mm + (k <= 3 ? -1 : 1) * dot_pitch_mm / 2, dot_pitch_mm * (1 - (k - 1) % 3), -dot_sink_mm])
            braille_dot();
}

// The label for number n, its front foot along y = 0 and centred on x = 0,
// standing on z = 0: the wedge, then the cells turned onto its sloped face.
module label_wedge(n) {
    cs = cells(n);
    w = label_w(cs);
    translate([-w / 2, 0, 0]) rotate([90, 0, 90])
        linear_extrude(height = w)
            polygon([[0, -0.01], [face_run_mm, wedge_h_mm], [face_run_mm + wedge_top_mm, wedge_h_mm], [wedge_depth_mm, -0.01]]);
    translate([0, cells_up_mm * cos(face_angle_deg), cells_up_mm * sin(face_angle_deg)])
        rotate([face_angle_deg, 0, 0])
            braille_cells(cs);
}

// The trace line's half-width at height z: a foot that flares out over the
// lower half, straight sides, then a rounded top that keeps a flat at least
// one 0.4 mm extrusion wide.
function trace_half_w(z) =
    let(w = trace_width_mm / 2, h = trace_height_mm, r = min(h / 2, (trace_width_mm - 0.4) / 2))
    z <= h / 2 ? w + trace_flare_mm * (1 - 2 * z / h)
    : z <= h - r ? w
    : w - r + sqrt(max(0, r * r - pow(z - (h - r), 2)));

// A raised line from the origin back along -y for `length`, standing on
// z = 0, running 1 mm past y = 0 into whatever stands there. Its profile is
// stacked from slices, each as wide as the smooth profile at its own top,
// so every slice sits on or just inside it (the plug puller's roundover).
module trace_line(length) {
    n = ceil(trace_height_mm / trace_slice_mm);
    dz = trace_height_mm / n;
    for (i = [0 : n - 1]) {
        z0 = i == 0 ? -0.01 : i * dz;
        z1 = (i + 1) * dz + (i < n - 1 ? 0.01 : 0);
        translate([0, 0, z0])
            linear_extrude(height = z1 - z0)
                offset(delta = trace_half_w((i + 1) * dz) - trace_width_mm / 2)
                    translate([-trace_width_mm / 2, -length]) square([trace_width_mm, length + 1]);
    }
}

module map_plate(p) {
    rows = plates[p - 1];
    w = plate_w(rows);
    h = plate_h(rows);
    echo(str("PLATE ", p, " (", plate_names[p - 1], "): ", w, " x ", h, " x ", plate_thickness_mm, " mm; top ", plate_top(rows), " mm; step ", level_step_mm, " mm; rows ", rows));
    difference() {
        union() {
            rounded_plate(w, h, plate_thickness_mm);
            for (r = [0 : len(rows) - 1]) {
                fs = rows[r];
                x0 = (w - row_width(fs)) / 2;          // each row centred across the plate
                y0 = row_y(rows, r);                    // the row's label baseline
                for (k = [0 : len(fs) - 1]) {
                    n = fs[k];
                    cx = x0 + face_x(fs, k) + face_w(n) / 2;
                    cy = y0 + label_band_mm + row_height(fs) / 2;
                    translate([cx, cy, 0]) face_shape(n);
                    translate([cx, y0 + (r == len(rows) - 1 ? notch_depth_mm + 1 : 1), 0]) numeral(n);
                    // The braille label stands label_gap_mm above the shape's top edge; on a
                    // plate with more than one shape, a line joins each label to its shape.
                    if (braille_labels)
                        translate([cx, cy + face_h(n) / 2 + label_gap_mm, plate_thickness_mm]) {
                            label_wedge(n);
                            if (len(fs) > 1) trace_line(label_gap_mm + 1);
                        }
                }
            }
        }
        // The notch tally of the row nearest the edge sits under its numerals;
        // an upper row's tally is cut as short grooves beside its numeral instead.
        last = rows[len(rows) - 1];
        for (k = [0 : len(last) - 1])
            edge_notches(last[k], (w - row_width(last)) / 2 + face_x(last, k) + face_w(last[k]) / 2);
        for (r = [0 : len(rows) - 2]) {
            fs = rows[r];
            for (k = [0 : len(fs) - 1])
                translate([(w - row_width(fs)) / 2 + face_x(fs, k) + face_w(fs[k]) / 2, row_y(rows, r) + 1 - 2.5, 0])
                    row_notches(fs[k]);
        }
    }
}

// An upper row's tally: the same count as short raised bars would be, cut
// as grooves into the plate under the numeral, one groove a count.
module row_notches(n) {
    span = (n - 1) * notch_pitch_mm;
    for (i = [0 : n - 1])
        translate([-span / 2 + i * notch_pitch_mm - notch_width_mm / 2, 0, plate_thickness_mm - notch_depth_mm / 2])
            cube([notch_width_mm, notch_depth_mm, plate_thickness_mm]);
}

// Where plate p starts in the all-plates preview: the plates stand in a row,
// notched edges in line, each clear of the one before.
function preview_x(p) = p <= 1 ? 0 : preview_x(p - 1) + plate_w(plates[p - 2]) + preview_gap_mm;

if (plate == 0) {
    for (p = [1 : len(plates)])
        translate([preview_x(p), 0, 0]) map_plate(p);
} else {
    map_plate(plate);
}
