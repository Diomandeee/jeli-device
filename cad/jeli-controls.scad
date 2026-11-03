include <jeli-config.scad>
use <jeli-primitives.scad>

module display_bezel() {
    difference() {
        rounded_box([bezel_outer_w, bezel_t, bezel_outer_h], 4);
        cube([display_open_w, bezel_t + 2, display_open_h], center = true);
    }
}

module display_bezel_print() {
    rotate([90, 0, 0]) display_bezel();
}

module camera_shutter() {
    union() {
        rounded_box([31, 2.0, 15], 2.0);
        translate([12, -1.7, 0]) rounded_box([7, 3.4, 7], 1.5);
    }
}

module camera_shutter_print() {
    rotate([90, 0, 0]) camera_shutter();
}

module talk_button() {
    difference() {
        union() {
            cylinder(h = 6.2, d = talk_button_d, center = true);
            translate([0, 0, -5]) cylinder(h = 6, d = 10, center = true);
        }
        // A shallow tactile bowl keeps the finger centered without looking.
        translate([0, 0, 12.4]) sphere(r = 10);
    }
}

module status_ring() {
    ring(status_ring_od, status_ring_id, 1.8);
}

module privacy_slider() {
    union() {
        rounded_box([5.2, 14.5, 5.2], 1.2);
        translate([3.1, 0, 0]) rounded_box([3.2, 9, 8], 1.1);
    }
}

module privacy_slider_print() {
    rotate([0, 90, 0]) privacy_slider();
}

module neck_yoke() {
    difference() {
        union() {
            cylinder(h = 5, d = 32);
            translate([0, 0, 11]) rounded_box([24, 18, 16], 3);
            translate([0, 0, 18]) rounded_box([118, 18, 8], 3);
            for (x = [-57.5, 57.5])
                translate([x, 0, 43]) rounded_box([7, 18, 54], 2.5);
        }
        translate([0, 0, 43]) x_cylinder(130, 5.0);
        // Servo lead path through the center post.
        translate([0, 0, 8]) cylinder(h = 20, d = 9, center = true);
    }
}

module fit_coupon() {
    difference() {
        rounded_prism([58, 24, 3], 3);
        translate([-18, 0, 0]) cylinder(h = 5, d = m3_clear_d, center = true);
        translate([0, 0, 0]) cylinder(h = 5, d = m3_insert_d, center = true);
        translate([18, 0, 0]) cube([13, 6, 5], center = true);
    }
}

module pi_carrier() {
    difference() {
        union() {
            rounded_prism(pi_carrier, 4);
            for (x = pi_hole_x)
                for (y = pi_hole_y)
                    translate([x, y, pi_carrier[2] / 2 + pi_standoff_h / 2])
                        cylinder(h = pi_standoff_h, d = pi_standoff_d, center = true);
        }

        for (x = pi_hole_x)
            for (y = pi_hole_y)
                translate([x, y, pi_standoff_h / 2])
                    cylinder(h = pi_carrier[2] + pi_standoff_h + 2, d = pi_mount_clear_d, center = true);

        // Concave corners clear the existing base shell bosses.
        for (x = [-48, 48])
            for (y = [-34, 34])
                translate([x, y, 0]) cylinder(h = pi_carrier[2] + 2, d = 14, center = true);

        // Two hook-and-loop/cable-tie slots make the prototype mount removable.
        for (x = [-33, 33])
            cube([3.2, 18, pi_carrier[2] + 2], center = true);
    }
}

module arducam_carrier() {
    difference() {
        rounded_prism(arducam_carrier, 3);
        cylinder(h = arducam_carrier[2] + 2, d = arducam_lens_clear_d, center = true);

        // Orthogonal strap slots allow the 34 mm board or its back cover to be
        // retained without assuming undocumented mounting-hole coordinates.
        for (x = [-19, 19])
            translate([x, 0, 0])
                cube([arducam_strap_slot[0], arducam_strap_slot[1], arducam_carrier[2] + 2], center = true);
        for (y = [-19, 19])
            translate([0, y, 0])
                cube([arducam_strap_slot[1], arducam_strap_slot[0], arducam_carrier[2] + 2], center = true);

        // Rotate the carrier so this service notch matches the owned USB-C side.
        translate([0, arducam_carrier[1] / 2, 0])
            cube([14, 8, arducam_carrier[2] + 2], center = true);
    }
}

module power_bank_sled() {
    difference() {
        rounded_prism(power_sled, 6);

        // Share the base's four underside screw positions with longer M3 screws.
        for (x = [-48, 48])
            for (y = [-34, 34])
                translate([x, y, 0])
                    cylinder(h = power_sled[2] + 2, d = m3_clear_d, center = true);

        // A replaceable hook-and-loop strap retains a certified power bank;
        // the lithium pack remains visible, removable, and unsealed.
        for (x = [-45, 45])
            translate([x, 0, 0])
                cube([power_strap_slot[0], power_strap_slot[1], power_sled[2] + 2], center = true);
    }
}

module nko_badge() {
    union() {
        rounded_box([50, 2.0, 16], 2.5);
        translate([0, -1.5, 0])
            rotate([90, 0, 0])
                linear_extrude(height = 1.2, center = true)
                    text(
                        "ߖߍߟߌ",
                        font = "Noto Sans NKo:style=Regular",
                        size = 10,
                        direction = "rtl",
                        halign = "center",
                        valign = "center"
                    );
    }
}

module nko_badge_print() {
    rotate([90, 0, 0]) nko_badge();
}
