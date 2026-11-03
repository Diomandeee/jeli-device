include <jeli-config.scad>
use <jeli-primitives.scad>

module head_skin() {
    difference() {
        rounded_box([head_w, head_d, head_h], head_radius);
        rounded_box(
            [head_w - 2 * wall, head_d - 2 * wall, head_h - 2 * wall],
            head_radius - wall
        );
    }
}

module head_pivot_cutouts() {
    translate([0, 0, head_pivot_z]) x_cylinder(head_w + 8, 6.4);
}

module front_join_bosses() {
    for (x = [-42, 42])
        for (z = [-29, 29])
            translate([x, -head_d / 4 + wall / 2, z])
                y_cylinder(head_d / 2 - wall, boss_d);
}

module rear_join_bosses() {
    for (x = [-42, 42])
        for (z = [-29, 29])
            translate([x, head_d / 4 - wall / 2, z])
                y_cylinder(head_d / 2 - wall, boss_d);
}

module head_front() {
    difference() {
        union() {
            intersection() {
                head_skin();
                half_space_y(true);
            }
            front_join_bosses();
            // Shutter rails, printed with the front shell.
            for (z = [camera_z - 9.2, camera_z + 9.2])
                translate([0, -head_d / 2 - 2.2 + shutter_rail_depth / 2, z])
                    rounded_box([43, shutter_rail_depth, 2.4], 0.8);
        }

        // Active display opening.
        translate([0, -head_d / 2, display_z])
            cube([display_open_w, wall + 8, display_open_h], center = true);

        // Camera window, deliberately coverable by a physical shutter.
        translate([0, -head_d / 2, camera_z])
            cube([camera_open_w, wall + 8, camera_open_h], center = true);

        head_pivot_cutouts();

        // Blind heat-set insert pockets entered from the center seam.
        for (x = [-42, 42])
            for (z = [-29, 29])
                translate([x, -m3_insert_depth / 2 + 0.1, z])
                    y_cylinder(m3_insert_depth + 0.4, m3_insert_d);
    }
}

module head_rear() {
    difference() {
        union() {
            intersection() {
                head_skin();
                half_space_y(false);
            }
            rear_join_bosses();
        }

        head_pivot_cutouts();

        // Rear-access M3 clearance paths into the front-half inserts.
        for (x = [-42, 42])
            for (z = [-29, 29])
                translate([x, head_d / 4 + wall, z])
                    y_cylinder(head_d / 2 + 2 * wall + 1, m3_clear_d);

        // Speaker grille: nine protected circular ports.
        for (x = [-14, 0, 14])
            for (z = [-25, -13, -1])
                translate([x, head_d / 2, z])
                    y_cylinder(wall + 8, 3.2);
    }
}

module base_skin() {
    difference() {
        rounded_box([base_w, base_d, base_h], base_radius);
        rounded_box(
            [base_w - 2 * wall, base_d - 2 * wall, base_h - 2 * wall],
            base_radius - wall
        );
    }
}

module base_top_bosses() {
    for (x = [-48, 48])
        for (y = [-34, 34])
            translate([x, y, (base_h / 2 - wall) / 2])
                cylinder(h = base_h / 2 - wall, d = boss_d, center = true);
}

module base_bottom_bosses() {
    for (x = [-48, 48])
        for (y = [-34, 34])
            translate([x, y, -(base_h / 2 - wall) / 2])
                cylinder(h = base_h / 2 - wall, d = boss_d, center = true);
}

module base_top() {
    difference() {
        union() {
            intersection() {
                base_skin();
                half_space_z(true);
            }
            base_top_bosses();
        }

        // Large, unmistakable press-to-talk control.
        translate([talk_button_x, talk_button_y, base_h / 2])
            cylinder(h = wall + 8, d = talk_button_clearance_d, center = true);

        // Status-light diffuser groove around the talk button.
        translate([talk_button_x, talk_button_y, base_h / 2 - 0.7])
            ring(status_ring_od + 0.5, status_ring_id - 0.5, 2.0);

        // NFC card landing zone; shallow enough to preserve the roof.
        translate([nfc_deck_x, nfc_deck_y, base_h / 2 - 0.55])
            rounded_prism([nfc_deck_w, nfc_deck_d, 1.3], 4);

        // Pan-servo / neck pass-through.
        translate([0, neck_y, base_h / 2])
            cylinder(h = wall + 8, d = neck_open_d, center = true);

        // Microphone aperture is isolated from the speaker in the head rear.
        translate([talk_button_x + 19, talk_button_y, base_h / 2])
            cylinder(h = wall + 8, d = 2.4, center = true);

        // Heat-set insert pockets entered from the horizontal seam.
        for (x = [-48, 48])
            for (y = [-34, 34])
                translate([x, y, m3_insert_depth / 2 - 0.1])
                    cylinder(h = m3_insert_depth + 0.4, d = m3_insert_d, center = true);
    }
}

module base_bottom() {
    difference() {
        union() {
            intersection() {
                base_skin();
                half_space_z(false);
            }
            base_bottom_bosses();
        }

        // M3 screw access from the underside.
        for (x = [-48, 48])
            for (y = [-34, 34])
                translate([x, y, -base_h / 4 - wall])
                    cylinder(h = base_h / 2 + 2 * wall + 1, d = m3_clear_d, center = true);

        // USB-C power and service access on the rear face.
        translate([0, base_d / 2, -8])
            cube([13, wall + 8, 6], center = true);

        // Hard privacy/power slider on the right side.
        translate([base_w / 2, 0, -7])
            cube([wall + 8, 16, 6], center = true);

        // Rear ventilation below the head speaker path.
        for (x = [-30, -20, -10, 10, 20, 30])
            translate([x, base_d / 2, -14])
                y_cylinder(wall + 8, 2.8);

        // Recessed rubber feet.
        for (x = [-45, 45])
            for (y = [-32, 32])
                translate([x, y, -base_h / 2 + 0.6])
                    cylinder(h = 1.4, d = 11, center = true);
    }
}
