// Jeli v0.1 — central dimensional contract (millimetres)
// Change component envelopes here before changing shell geometry.

$fn = 48;

wall = 2.6;
fit_clearance = 0.35;
seam_clearance = 0.30;

// Friendly, compact tabletop scale. Every part fits a 220 x 220 mm bed.
base_w = 124;
base_d = 100;
base_h = 46;
base_radius = 12;

head_w = 108;
head_d = 76;
head_h = 86;
head_radius = 14;

// Head face.
display_open_w = 58;
display_open_h = 38;
display_z = 3;
camera_open_w = 13;
camera_open_h = 9;
camera_z = 31;
// V2.1: bridge the curved forehead so both shutter rails join the shell.
shutter_rail_depth = 12;
bezel_outer_w = 66;
bezel_outer_h = 46;
bezel_t = 2.4;

// Learning deck.
talk_button_d = 28;
talk_button_clearance_d = 29.0;
talk_button_x = -34;
talk_button_y = -22;
status_ring_od = 36;
status_ring_id = 30;
nfc_deck_w = 50;
nfc_deck_d = 40;
nfc_deck_x = 29;
nfc_deck_y = -8;
neck_y = 30;
neck_open_d = 34;

// Fasteners and printable joinery.
m3_clear_d = 3.4;
m3_insert_d = 4.2;
m3_insert_depth = 5.5;
boss_d = 10;

// Proxy hardware envelopes — verify against the purchased parts before final print.
display_pcb = [64, 8, 48];
// B0478 board width/height are documented as 34 mm. Depth remains a generous
// prototype proxy until Mohamed measures the owned back-cover/lens assembly.
camera_pcb = [34, 12, 34];
esp32_s3_pcb = [58, 28, 15];
pn532_pcb = [50, 40, 6];
sg90_body = [23, 12.2, 29];
speaker_d = 40;
speaker_depth = 14;

// Reversible first-prototype carriers. The Pi hole coordinates mirror the
// standard Model B footprint while leaving the exact owned Pi as a fit gate.
pi_board = [85, 56, 1.6];
pi_operating_envelope = [85, 56, 22];
pi_carrier = [92, 64, 3];
pi_hole_x = [-39, 19];
pi_hole_y = [-24.5, 24.5];
pi_mount_clear_d = 2.8;
pi_standoff_d = 6.4;
pi_standoff_h = 5;

arducam_carrier = [44, 44, 3];
arducam_lens_clear_d = 18;
arducam_strap_slot = [3.2, 18];

power_bank_proxy = [105, 68, 24];
power_sled = [112, 82, 3];
power_strap_slot = [4, 24];

// Assembly locations.
assembly_base_z = base_h / 2;
assembly_head_y = 30;
assembly_head_z = 107;
assembly_yoke_z = base_h;
head_pivot_z = -18;

// Product palette (render only).
shell_color = [0.055, 0.16, 0.13];
shell_rear_color = [0.035, 0.09, 0.08];
accent_color = [0.95, 0.57, 0.12];
screen_color = [0.02, 0.035, 0.03];
privacy_color = [0.77, 0.16, 0.10];
component_color = [0.18, 0.28, 0.33, 0.50];
