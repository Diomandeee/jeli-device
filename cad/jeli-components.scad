include <jeli-config.scad>
use <jeli-primitives.scad>

// These are collision proxies, not vendor CAD. Their only authority is the
// dimensional contract in jeli-config.scad.

module display_proxy() {
    color([0.08, 0.32, 0.24, 0.72])
        rounded_box(display_pcb, 2);
}

module camera_proxy() {
    color([0.12, 0.12, 0.14, 0.72]) {
        rounded_box(camera_pcb, 2);
        translate([0, -(camera_pcb[1] / 2 + 9), 0]) y_cylinder(18, arducam_lens_clear_d - 4);
    }
}

module esp32_proxy() {
    color([0.08, 0.30, 0.42, 0.72]) rounded_box(esp32_s3_pcb, 2);
}

module pn532_proxy() {
    color([0.58, 0.36, 0.05, 0.60]) rounded_box(pn532_pcb, 2);
}

module sg90_proxy() {
    color([0.10, 0.32, 0.72, 0.65]) rounded_box(sg90_body, 1.5);
}

module speaker_proxy() {
    color([0.20, 0.20, 0.20, 0.72]) y_cylinder(speaker_depth, speaker_d);
}

module pi_proxy() {
    color([0.07, 0.38, 0.18, 0.66]) rounded_box(pi_operating_envelope, 2);
}

module power_bank_proxy() {
    color([0.28, 0.28, 0.30, 0.52]) rounded_box(power_bank_proxy, 4);
}

module head_component_pack() {
    translate([0, -head_d / 2 + wall + display_pcb[1] / 2 + 1, display_z]) display_proxy();
    // The B0478 sits behind the display PCB plane; its lens reaches the front
    // window without forcing the 34 mm board into the display envelope.
    translate([0, -15, camera_z]) camera_proxy();
    translate([0, head_d / 2 - wall - speaker_depth / 2, -16]) speaker_proxy();
}

module base_component_pack() {
    translate([nfc_deck_x, nfc_deck_y, base_h / 2 - wall - pn532_pcb[2] / 2]) pn532_proxy();
    translate([0, neck_y, 1]) sg90_proxy();
    translate([0, -6, -8]) pi_proxy();
}
