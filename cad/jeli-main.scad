include <jeli-config.scad>
use <jeli-primitives.scad>
use <jeli-shell.scad>
use <jeli-controls.scad>
use <jeli-components.scad>

part = is_undef(part) ? "assembly" : part;
show_components = is_undef(show_components) ? false : show_components;

module assembled(exploded = 0, components = false) {
    // The two shell families use independent seams so the electronics remain
    // accessible without disturbing the pitch/yaw cradle.
    color(shell_rear_color)
        translate([0, 0, assembly_base_z - exploded / 2]) base_bottom();
    color(shell_color)
        translate([0, 0, assembly_base_z + exploded / 2]) base_top();

    color(accent_color)
        translate([talk_button_x, talk_button_y, base_h + 2.2 + exploded / 2]) talk_button();
    color([1.0, 0.72, 0.20, 0.72])
        translate([talk_button_x, talk_button_y, base_h + 1.0 + exploded / 2]) status_ring();
    color(privacy_color)
        translate([base_w / 2 + 2.2 + exploded / 2, 0, 16]) privacy_slider();
    color(accent_color)
        translate([0, -base_d / 2 - 1.5 - exploded / 2, 17]) nko_badge();

    color([0.11, 0.18, 0.16])
        translate([0, assembly_head_y, assembly_yoke_z + exploded / 2]) neck_yoke();

    color(shell_color)
        translate([0, assembly_head_y - exploded / 2, assembly_head_z]) head_front();
    color(shell_rear_color)
        translate([0, assembly_head_y + exploded / 2, assembly_head_z]) head_rear();

    color(accent_color)
        translate([
            0,
            assembly_head_y - head_d / 2 - bezel_t / 2 - 0.25 - exploded / 2,
            assembly_head_z + display_z
        ]) display_bezel();
    color([0.04, 0.055, 0.045])
        translate([
            0,
            assembly_head_y - head_d / 2 - 0.15 - exploded / 2,
            assembly_head_z + display_z
        ]) cube([display_open_w - 1, 0.9, display_open_h - 1], center = true);
    color(privacy_color)
        translate([
            -8,
            assembly_head_y - head_d / 2 - 2.3 - exploded / 2,
            assembly_head_z + camera_z
        ]) camera_shutter();

    if (components) {
        translate([0, assembly_head_y, assembly_head_z]) head_component_pack();
        translate([0, 0, assembly_base_z]) base_component_pack();
    }
}

if (part == "assembly") {
    assembled(false, show_components);
} else if (part == "exploded") {
    assembled(12, show_components);
} else if (part == "assembly_components") {
    assembled(8, true);
} else if (part == "head_front") {
    translate([0, 0, head_d / 2 + 2.5]) rotate([90, 0, 0]) head_front();
} else if (part == "head_rear") {
    translate([0, 0, head_d / 2]) rotate([-90, 0, 0]) head_rear();
} else if (part == "base_top") {
    translate([0, 0, base_h / 2]) rotate([180, 0, 0]) base_top();
} else if (part == "base_bottom") {
    translate([0, 0, base_h / 2]) base_bottom();
} else if (part == "neck_yoke") {
    neck_yoke();
} else if (part == "display_bezel") {
    translate([0, 0, bezel_t / 2]) display_bezel_print();
} else if (part == "camera_shutter") {
    translate([0, 0, 2]) camera_shutter_print();
} else if (part == "talk_button") {
    translate([0, 0, 8]) talk_button();
} else if (part == "status_ring") {
    translate([0, 0, 0.9]) status_ring();
} else if (part == "privacy_slider") {
    translate([0, 0, 3]) privacy_slider_print();
} else if (part == "nko_badge") {
    translate([0, 0, 2.5]) nko_badge_print();
} else if (part == "fit_coupon") {
    translate([0, 0, 1.5]) fit_coupon();
} else if (part == "pi_carrier") {
    translate([0, 0, pi_carrier[2] / 2]) pi_carrier();
} else if (part == "arducam_carrier") {
    translate([0, 0, arducam_carrier[2] / 2]) arducam_carrier();
} else if (part == "power_bank_sled") {
    translate([0, 0, power_sled[2] / 2]) power_bank_sled();
} else {
    assert(false, str("Unknown part selector: ", part));
}
