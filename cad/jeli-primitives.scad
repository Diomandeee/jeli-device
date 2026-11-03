include <jeli-config.scad>

module rounded_box(size, radius, center = true) {
    sx = size[0];
    sy = size[1];
    sz = size[2];
    assert(min(size) > 2 * radius, "rounded_box radius exceeds part size");
    translate(center ? [0, 0, 0] : [sx / 2, sy / 2, sz / 2])
        hull()
            for (x = [-sx / 2 + radius, sx / 2 - radius])
                for (y = [-sy / 2 + radius, sy / 2 - radius])
                    for (z = [-sz / 2 + radius, sz / 2 - radius])
                        translate([x, y, z]) sphere(r = radius);
}

module rounded_prism(size, radius, center = true) {
    translate(center ? [0, 0, 0] : [size[0] / 2, size[1] / 2, size[2] / 2])
        linear_extrude(height = size[2], center = true)
            offset(r = radius)
                square([size[0] - 2 * radius, size[1] - 2 * radius], center = true);
}

module y_cylinder(h, d, center = true) {
    rotate([90, 0, 0]) cylinder(h = h, d = d, center = center);
}

module x_cylinder(h, d, center = true) {
    rotate([0, 90, 0]) cylinder(h = h, d = d, center = center);
}

module ring(od, id, h) {
    difference() {
        cylinder(d = od, h = h, center = true);
        cylinder(d = id, h = h + 1, center = true);
    }
}

module half_space_y(front = true) {
    translate([0, front ? -100 : 100, 0]) cube([400, 200, 400], center = true);
}

module half_space_z(top = true) {
    translate([0, 0, top ? 100 : -100]) cube([400, 400, 200], center = true);
}

