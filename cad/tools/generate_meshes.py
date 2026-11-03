#!/usr/bin/env python3
"""Generate Jeli printable meshes and review renders with manifold3d.

The OpenSCAD files remain the human-editable dimensional source. This generator
mirrors that contract so exports do not depend on a macOS GUI bundle launching.
"""

from __future__ import annotations

import json
import os
import math
import operator
import re
import sys
from dataclasses import dataclass
from functools import reduce
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from manifold3d import CrossSection, Manifold


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
RENDERS = ROOT / "renders"

WALL = 2.6
BASE = (124.0, 100.0, 46.0)
BASE_RADIUS = 12.0
HEAD = (108.0, 76.0, 86.0)
HEAD_RADIUS = 14.0
DISPLAY_OPEN = (58.0, 38.0)
DISPLAY_Z = 3.0
CAMERA_OPEN = (13.0, 9.0)
CAMERA_Z = 31.0
SHUTTER_RAIL_DEPTH = 12.0
BEZEL = (66.0, 2.4, 46.0)
TALK_D = 28.0
TALK_CLEAR_D = 29.0
TALK_X = -34.0
TALK_Y = -22.0
STATUS_OD = 36.0
STATUS_ID = 30.0
NFC_DECK = (50.0, 40.0)
NFC_X = 29.0
NFC_Y = -8.0
NECK_Y = 30.0
NECK_OPEN_D = 34.0
M3_CLEAR_D = 3.4
M3_INSERT_D = 4.2
M3_INSERT_DEPTH = 5.5
BOSS_D = 10.0
ASSEMBLY_HEAD_Y = 30.0
ASSEMBLY_HEAD_Z = 107.0
HEAD_PIVOT_Z = -18.0
CAMERA_PCB = (34.0, 12.0, 34.0)
PI_BOARD = (85.0, 56.0, 1.6)
PI_ENVELOPE = (85.0, 56.0, 22.0)
PI_CARRIER = (92.0, 64.0, 3.0)
PI_HOLE_X = (-39.0, 19.0)
PI_HOLE_Y = (-24.5, 24.5)
PI_MOUNT_CLEAR_D = 2.8
PI_STANDOFF_D = 6.4
PI_STANDOFF_H = 5.0
ARDUCAM_CARRIER = (44.0, 44.0, 3.0)
ARDUCAM_LENS_CLEAR_D = 18.0
ARDUCAM_STRAP_SLOT = (3.2, 18.0)
POWER_BANK = (105.0, 68.0, 24.0)
POWER_SLED = (112.0, 82.0, 3.0)
POWER_STRAP_SLOT = (4.0, 24.0)

COLORS = {
    "shell": (14, 48, 38),
    "rear": (8, 26, 23),
    "accent": (242, 145, 31),
    "privacy": (196, 40, 26),
    "screen": (5, 10, 8),
    "component": (55, 105, 118),
    "nfc": (176, 111, 26),
}


def assert_scad_parity():
    """Fail closed if the readable SCAD contract and exporter have drifted."""
    text = (ROOT / "jeli-config.scad").read_text()
    scalars = {
        name: float(value)
        for name, value in re.findall(r"^([a-zA-Z0-9_]+)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\s*;", text, re.MULTILINE)
    }
    expected = {
        "wall": WALL,
        "base_w": BASE[0],
        "base_d": BASE[1],
        "base_h": BASE[2],
        "base_radius": BASE_RADIUS,
        "head_w": HEAD[0],
        "head_d": HEAD[1],
        "head_h": HEAD[2],
        "head_radius": HEAD_RADIUS,
        "display_open_w": DISPLAY_OPEN[0],
        "display_open_h": DISPLAY_OPEN[1],
        "camera_open_w": CAMERA_OPEN[0],
        "camera_open_h": CAMERA_OPEN[1],
        "shutter_rail_depth": SHUTTER_RAIL_DEPTH,
        "talk_button_d": TALK_D,
        "talk_button_x": TALK_X,
        "talk_button_y": TALK_Y,
        "nfc_deck_w": NFC_DECK[0],
        "nfc_deck_d": NFC_DECK[1],
        "nfc_deck_x": NFC_X,
        "nfc_deck_y": NFC_Y,
        "neck_y": NECK_Y,
        "neck_open_d": NECK_OPEN_D,
        "pi_mount_clear_d": PI_MOUNT_CLEAR_D,
        "pi_standoff_d": PI_STANDOFF_D,
        "pi_standoff_h": PI_STANDOFF_H,
        "arducam_lens_clear_d": ARDUCAM_LENS_CLEAR_D,
    }
    drift = {
        key: {"scad": scalars.get(key), "generator": value}
        for key, value in expected.items()
        if scalars.get(key) != value
    }
    if drift:
        raise RuntimeError(f"jeli-config.scad parity failure: {json.dumps(drift, sort_keys=True)}")


def union(items):
    items = list(items)
    if not items:
        return Manifold()
    return reduce(operator.add, items)


def cube(size, at=(0.0, 0.0, 0.0)):
    return Manifold.cube(size, center=True).translate(at)


def cylinder(height, diameter, at=(0.0, 0.0, 0.0), axis="z", segments=48):
    result = Manifold.cylinder(height, diameter / 2, circular_segments=segments, center=True)
    if axis == "x":
        result = result.rotate((0, 90, 0))
    elif axis == "y":
        result = result.rotate((90, 0, 0))
    return result.translate(at)


def rounded_box(size, radius, at=(0.0, 0.0, 0.0), segments=24):
    sx, sy, sz = size
    if min(size) <= radius * 2:
        radius = min(size) / 2 - 0.01
    seed = Manifold.sphere(radius, circular_segments=segments)
    corners = []
    for x in (-sx / 2 + radius, sx / 2 - radius):
        for y in (-sy / 2 + radius, sy / 2 - radius):
            for z in (-sz / 2 + radius, sz / 2 - radius):
                corners.append(seed.translate((x, y, z)))
    return Manifold.batch_hull(corners).translate(at)


def ring(outer_d, inner_d, height, at=(0.0, 0.0, 0.0)):
    return cylinder(height, outer_d, at) - cylinder(height + 1.0, inner_d, at)


def head_skin():
    outer = rounded_box(HEAD, HEAD_RADIUS)
    inner = rounded_box(
        tuple(value - 2 * WALL for value in HEAD),
        HEAD_RADIUS - WALL,
    )
    return outer - inner


def head_front_and_rear():
    head_w, head_d, _ = HEAD
    skin = head_skin()
    front_clip = cube((300, head_d / 2, 300), (0, -head_d / 4, 0))
    rear_clip = cube((300, head_d / 2, 300), (0, head_d / 4, 0))

    front_bosses = []
    rear_bosses = []
    for x in (-42, 42):
        for z in (-29, 29):
            front_bosses.append(
                cylinder(head_d / 2 - WALL, BOSS_D, (x, -head_d / 4 + WALL / 2, z), "y")
            )
            rear_bosses.append(
                cylinder(head_d / 2 - WALL, BOSS_D, (x, head_d / 4 - WALL / 2, z), "y")
            )

    rails = [
        rounded_box(
            (43, SHUTTER_RAIL_DEPTH, 2.4), 0.8,
            (0, -head_d / 2 - 2.2 + SHUTTER_RAIL_DEPTH / 2, z),
        )
        for z in (CAMERA_Z - 9.2, CAMERA_Z + 9.2)
    ]

    front = (skin ^ front_clip) + union(front_bosses) + union(rails)
    front -= cube((DISPLAY_OPEN[0], WALL + 8, DISPLAY_OPEN[1]), (0, -head_d / 2, DISPLAY_Z))
    front -= cube((CAMERA_OPEN[0], WALL + 8, CAMERA_OPEN[1]), (0, -head_d / 2, CAMERA_Z))
    front -= cylinder(head_w + 8, 6.4, (0, 0, HEAD_PIVOT_Z), "x")
    for x in (-42, 42):
        for z in (-29, 29):
            front -= cylinder(
                M3_INSERT_DEPTH + 0.4,
                M3_INSERT_D,
                (x, -M3_INSERT_DEPTH / 2 + 0.1, z),
                "y",
            )

    rear = (skin ^ rear_clip) + union(rear_bosses)
    rear -= cylinder(head_w + 8, 6.4, (0, 0, HEAD_PIVOT_Z), "x")
    for x in (-42, 42):
        for z in (-29, 29):
            rear -= cylinder(
                head_d / 2 + 2 * WALL + 1,
                M3_CLEAR_D,
                (x, head_d / 4 + WALL, z),
                "y",
            )
    for x in (-14, 0, 14):
        for z in (-25, -13, -1):
            rear -= cylinder(WALL + 8, 3.2, (x, head_d / 2, z), "y")
    return front, rear


def base_skin():
    outer = rounded_box(BASE, BASE_RADIUS)
    inner = rounded_box(tuple(value - 2 * WALL for value in BASE), BASE_RADIUS - WALL)
    return outer - inner


def base_top_and_bottom():
    base_w, base_d, base_h = BASE
    skin = base_skin()
    top_clip = cube((300, 300, base_h / 2), (0, 0, base_h / 4))
    bottom_clip = cube((300, 300, base_h / 2), (0, 0, -base_h / 4))

    top_bosses = []
    bottom_bosses = []
    boss_h = base_h / 2 - WALL
    for x in (-48, 48):
        for y in (-34, 34):
            top_bosses.append(cylinder(boss_h, BOSS_D, (x, y, boss_h / 2)))
            bottom_bosses.append(cylinder(boss_h, BOSS_D, (x, y, -boss_h / 2)))

    top = (skin ^ top_clip) + union(top_bosses)
    top -= cylinder(WALL + 8, TALK_CLEAR_D, (TALK_X, TALK_Y, base_h / 2))
    top -= ring(STATUS_OD + 0.5, STATUS_ID - 0.5, 2.0, (TALK_X, TALK_Y, base_h / 2 - 0.7))
    top -= rounded_box((NFC_DECK[0], NFC_DECK[1], 1.3), 0.64, (NFC_X, NFC_Y, base_h / 2 - 0.55))
    top -= cylinder(WALL + 8, NECK_OPEN_D, (0, NECK_Y, base_h / 2))
    top -= cylinder(WALL + 8, 2.4, (TALK_X + 19, TALK_Y, base_h / 2))
    for x in (-48, 48):
        for y in (-34, 34):
            top -= cylinder(M3_INSERT_DEPTH + 0.4, M3_INSERT_D, (x, y, M3_INSERT_DEPTH / 2 - 0.1))

    bottom = (skin ^ bottom_clip) + union(bottom_bosses)
    for x in (-48, 48):
        for y in (-34, 34):
            bottom -= cylinder(base_h / 2 + 2 * WALL + 1, M3_CLEAR_D, (x, y, -base_h / 4 - WALL))
    bottom -= cube((13, WALL + 8, 6), (0, base_d / 2, -8))
    bottom -= cube((WALL + 8, 16, 6), (base_w / 2, 0, -7))
    for x in (-30, -20, -10, 10, 20, 30):
        bottom -= cylinder(WALL + 8, 2.8, (x, base_d / 2, -14), "y")
    for x in (-45, 45):
        for y in (-32, 32):
            bottom -= cylinder(1.4, 11, (x, y, -base_h / 2 + 0.6))
    return top, bottom


def controls():
    bezel = rounded_box(BEZEL, 2.39) - cube((DISPLAY_OPEN[0], BEZEL[1] + 2, DISPLAY_OPEN[1]))
    shutter = rounded_box((31, 2.0, 15), 0.99) + rounded_box((7, 3.4, 7), 1.5, (12, -1.7, 0))
    button = cylinder(6.2, TALK_D) + cylinder(6, 10, (0, 0, -5))
    button -= Manifold.sphere(10, circular_segments=48).translate((0, 0, 12.4))
    status = ring(STATUS_OD, STATUS_ID, 1.8)
    privacy = rounded_box((5.2, 14.5, 5.2), 1.2) + rounded_box((3.2, 9, 8), 1.1, (3.1, 0, 0))

    yoke = union(
        [
            cylinder(5, 32, (0, 0, 2.5)),
            rounded_box((24, 18, 16), 3, (0, 0, 11)),
            rounded_box((118, 18, 8), 3, (0, 0, 18)),
            rounded_box((7, 18, 54), 2.5, (-57.5, 0, 43)),
            rounded_box((7, 18, 54), 2.5, (57.5, 0, 43)),
        ]
    )
    yoke -= cylinder(130, 5.0, (0, 0, 43), "x")
    yoke -= cylinder(20, 9, (0, 0, 8))

    coupon = rounded_box((58, 24, 3), 1.49)
    coupon -= cylinder(5, M3_CLEAR_D, (-18, 0, 0))
    coupon -= cylinder(5, M3_INSERT_D, (0, 0, 0))
    coupon -= cube((13, 6, 5), (18, 0, 0))
    badge = nko_badge()
    return bezel, shutter, button, status, privacy, yoke, coupon, badge


def prototype_accessories():
    pi_plate = rounded_box(PI_CARRIER, 1.49)
    pi_bosses = []
    for x in PI_HOLE_X:
        for y in PI_HOLE_Y:
            pi_bosses.append(
                cylinder(
                    PI_STANDOFF_H,
                    PI_STANDOFF_D,
                    (x, y, PI_CARRIER[2] / 2 + PI_STANDOFF_H / 2),
                )
            )
    pi_tray = pi_plate + union(pi_bosses)
    for x in PI_HOLE_X:
        for y in PI_HOLE_Y:
            pi_tray -= cylinder(
                PI_CARRIER[2] + PI_STANDOFF_H + 2,
                PI_MOUNT_CLEAR_D,
                (x, y, PI_STANDOFF_H / 2),
            )
    for x in (-48, 48):
        for y in (-34, 34):
            pi_tray -= cylinder(PI_CARRIER[2] + 2, 14, (x, y, 0))
    for x in (-33, 33):
        pi_tray -= cube((3.2, 18, PI_CARRIER[2] + 2), (x, 0, 0))

    camera_tray = rounded_box(ARDUCAM_CARRIER, 1.49)
    camera_tray -= cylinder(ARDUCAM_CARRIER[2] + 2, ARDUCAM_LENS_CLEAR_D)
    for x in (-19, 19):
        camera_tray -= cube(
            (ARDUCAM_STRAP_SLOT[0], ARDUCAM_STRAP_SLOT[1], ARDUCAM_CARRIER[2] + 2),
            (x, 0, 0),
        )
    for y in (-19, 19):
        camera_tray -= cube(
            (ARDUCAM_STRAP_SLOT[1], ARDUCAM_STRAP_SLOT[0], ARDUCAM_CARRIER[2] + 2),
            (0, y, 0),
        )
    camera_tray -= cube(
        (14, 8, ARDUCAM_CARRIER[2] + 2),
        (0, ARDUCAM_CARRIER[1] / 2, 0),
    )

    power_tray = rounded_box(POWER_SLED, 1.49)
    for x in (-48, 48):
        for y in (-34, 34):
            power_tray -= cylinder(POWER_SLED[2] + 2, M3_CLEAR_D, (x, y, 0))
    for x in (-45, 45):
        power_tray -= cube(
            (POWER_STRAP_SLOT[0], POWER_STRAP_SLOT[1], POWER_SLED[2] + 2),
            (x, 0, 0),
        )

    return pi_tray, camera_tray, power_tray


def nko_badge():
    plate = rounded_box((50, 16, 2), 0.99, (0, 0, 1.0))
    font_path = Path(os.environ.get("JELI_NKO_FONT", "/System/Library/Fonts/Supplemental/NotoSansNKo-Regular.ttf"))
    if not font_path.exists():
        return plate

    canvas = Image.new("L", (400, 120), 0)
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(font_path), 74)
    text = "ߖߍߟߌ"
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text(((400 - width) / 2 - bbox[0], (120 - height) / 2 - bbox[1]), text, fill=255, font=font)
    pixels = np.asarray(canvas) > 96
    ys, xs = np.nonzero(pixels)
    if not len(xs):
        return plate

    scale = min(44.0 / (xs.max() - xs.min() + 1), 10.5 / (ys.max() - ys.min() + 1))
    contours = []
    for row in range(ys.min(), ys.max() + 1):
        columns = np.where(pixels[row])[0]
        if not len(columns):
            continue
        start = previous = int(columns[0])
        for value in [*map(int, columns[1:]), None]:
            if value is None or value != previous + 1:
                x0 = (start - (xs.min() + xs.max() + 1) / 2) * scale
                x1 = (previous + 1 - (xs.min() + xs.max() + 1) / 2) * scale
                y0 = ((ys.min() + ys.max() + 1) / 2 - (row + 1)) * scale
                y1 = ((ys.min() + ys.max() + 1) / 2 - row) * scale
                contours.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                if value is not None:
                    start = value
            if value is not None:
                previous = value
    glyphs = CrossSection(contours).extrude(0.85).translate((0, 0, 2.0))
    return plate + glyphs


def component_proxies():
    return {
        "display": rounded_box((64, 8, 48), 2, (0, -HEAD[1] / 2 + WALL + 5, DISPLAY_Z)),
        "camera": rounded_box(CAMERA_PCB, 2, (0, -15, CAMERA_Z))
        + cylinder(18, ARDUCAM_LENS_CLEAR_D - 4, (0, -30, CAMERA_Z), "y"),
        "speaker": cylinder(14, 40, (0, HEAD[1] / 2 - WALL - 7, -16), "y"),
        "nfc": rounded_box((50, 40, 6), 2, (NFC_X, NFC_Y, BASE[2] / 2 - WALL - 3)),
        "servo": rounded_box((23, 12.2, 29), 1.5, (0, NECK_Y, 1)),
        "pi": rounded_box(PI_ENVELOPE, 2, (0, -6, -8)),
        "power_bank": rounded_box(POWER_BANK, 4),
    }


def to_bed(model):
    bounds = np.asarray(model.bounding_box(), dtype=float)
    lower = bounds[0] if bounds.shape == (2, 3) else bounds[:3]
    return model.translate((0, 0, -float(lower[2])))


def mesh_from_manifold(model):
    raw = model.to_mesh()
    mesh = trimesh.Trimesh(
        vertices=np.asarray(raw.vert_properties)[:, :3],
        faces=np.asarray(raw.tri_verts),
        process=False,
        validate=False,
    )
    return mesh


@dataclass
class RenderItem:
    model: Manifold
    color: tuple[int, int, int]


def render(items, path, camera=(235, -270, 205), target=(0, 0, 72), size=(1600, 1200)):
    width, height = size
    camera = np.asarray(camera, dtype=float)
    target = np.asarray(target, dtype=float)
    forward = target - camera
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    focal = width * 0.96
    light = np.array([-0.35, -0.55, 0.76])
    light /= np.linalg.norm(light)

    image = Image.new("RGB", size, (233, 229, 216))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((180, height - 220, width - 120, height - 75), fill=(40, 35, 30, 28))
    triangles = []

    for item in items:
        mesh = mesh_from_manifold(item.model)
        vertices = np.asarray(mesh.vertices)
        relative = vertices - camera
        cx = relative @ right
        cy = relative @ up
        depth = relative @ forward
        projected = np.column_stack((width / 2 + focal * cx / depth, height / 2 - focal * cy / depth))
        for face in np.asarray(mesh.faces):
            face_depth = float(depth[face].mean())
            if face_depth <= 1:
                continue
            world = vertices[face]
            normal = np.cross(world[1] - world[0], world[2] - world[0])
            norm = np.linalg.norm(normal)
            if norm == 0:
                continue
            normal /= norm
            shade = 0.56 + 0.44 * abs(float(normal @ light))
            color = tuple(max(0, min(255, int(value * shade))) for value in item.color)
            points = [tuple(projected[index]) for index in face]
            triangles.append((face_depth, points, color))

    for _, points, color in sorted(triangles, key=lambda record: record[0], reverse=True):
        draw.polygon(points, fill=(*color, 255), outline=(8, 12, 10, 42))

    image.save(path)


def build():
    assert_scad_parity()
    EXPORTS.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)

    head_front, head_rear = head_front_and_rear()
    base_top, base_bottom = base_top_and_bottom()
    bezel, shutter, button, status, privacy, yoke, coupon, badge = controls()
    pi_tray, camera_tray, power_tray = prototype_accessories()
    learning_card = rounded_box((46, 34, 1.4), 0.69)
    learning_card_mark = badge.scale((0.68, 0.68, 0.45))

    printable = {
        "head_front": to_bed(head_front.rotate((90, 0, 0))),
        "head_rear": to_bed(head_rear.rotate((-90, 0, 0))),
        "base_top": to_bed(base_top.rotate((180, 0, 0))),
        "base_bottom": to_bed(base_bottom),
        "neck_yoke": to_bed(yoke),
        "display_bezel": to_bed(bezel.rotate((90, 0, 0))),
        "camera_shutter": to_bed(shutter.rotate((90, 0, 0))),
        "talk_button": to_bed(button),
        "status_ring": to_bed(status),
        "privacy_slider": to_bed(privacy.rotate((0, 90, 0))),
        "nko_badge": to_bed(badge),
        "fit_coupon": to_bed(coupon),
        "pi_carrier": to_bed(pi_tray),
        "arducam_carrier": to_bed(camera_tray),
        "power_bank_sled": to_bed(power_tray),
    }

    for name, model in printable.items():
        mesh = mesh_from_manifold(model)
        mesh.export(EXPORTS / f"{name}.stl", file_type="stl")

    assembly = [
        RenderItem(base_bottom.translate((0, 0, BASE[2] / 2)), COLORS["rear"]),
        RenderItem(base_top.translate((0, 0, BASE[2] / 2)), COLORS["shell"]),
        RenderItem(button.translate((TALK_X, TALK_Y, BASE[2] + 2.2)), COLORS["accent"]),
        RenderItem(status.translate((TALK_X, TALK_Y, BASE[2] + 1.0)), (255, 190, 54)),
        RenderItem(learning_card.translate((NFC_X, NFC_Y, BASE[2] + 1.2)), (225, 210, 165)),
        RenderItem(learning_card_mark.translate((NFC_X, NFC_Y, BASE[2] + 2.0)), COLORS["accent"]),
        RenderItem(privacy.translate((BASE[0] / 2 + 2.2, 0, 16)), COLORS["privacy"]),
        RenderItem(badge.rotate((90, 0, 0)).translate((0, -BASE[1] / 2 - 1.5, 17)), COLORS["accent"]),
        RenderItem(yoke.translate((0, ASSEMBLY_HEAD_Y, BASE[2])), (28, 48, 42)),
        RenderItem(head_front.translate((0, ASSEMBLY_HEAD_Y, ASSEMBLY_HEAD_Z)), COLORS["shell"]),
        RenderItem(head_rear.translate((0, ASSEMBLY_HEAD_Y, ASSEMBLY_HEAD_Z)), COLORS["rear"]),
        RenderItem(
            bezel.translate((0, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - BEZEL[1] / 2 - 0.25, ASSEMBLY_HEAD_Z + DISPLAY_Z)),
            COLORS["accent"],
        ),
        RenderItem(
            cube((DISPLAY_OPEN[0] - 1, 0.9, DISPLAY_OPEN[1] - 1), (0, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - 0.15, ASSEMBLY_HEAD_Z + DISPLAY_Z)),
            COLORS["screen"],
        ),
        RenderItem(
            shutter.translate((-8, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - 2.3, ASSEMBLY_HEAD_Z + CAMERA_Z)),
            COLORS["privacy"],
        ),
    ]
    render(assembly, RENDERS / "jeli-assembly-3q.png")

    exploded = [
        RenderItem(base_bottom.translate((0, 0, BASE[2] / 2 - 6)), COLORS["rear"]),
        RenderItem(base_top.translate((0, 0, BASE[2] / 2 + 6)), COLORS["shell"]),
        RenderItem(button.translate((TALK_X, TALK_Y, BASE[2] + 8.2)), COLORS["accent"]),
        RenderItem(status.translate((TALK_X, TALK_Y, BASE[2] + 7.0)), (255, 190, 54)),
        RenderItem(learning_card.translate((NFC_X, NFC_Y, BASE[2] + 13.0)), (225, 210, 165)),
        RenderItem(learning_card_mark.translate((NFC_X, NFC_Y, BASE[2] + 13.8)), COLORS["accent"]),
        RenderItem(yoke.translate((0, ASSEMBLY_HEAD_Y, BASE[2] + 6)), (28, 48, 42)),
        RenderItem(head_front.translate((0, ASSEMBLY_HEAD_Y - 8, ASSEMBLY_HEAD_Z)), COLORS["shell"]),
        RenderItem(head_rear.translate((0, ASSEMBLY_HEAD_Y + 8, ASSEMBLY_HEAD_Z)), COLORS["rear"]),
        RenderItem(
            bezel.translate((0, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - 10, ASSEMBLY_HEAD_Z + DISPLAY_Z)),
            COLORS["accent"],
        ),
        RenderItem(
            shutter.translate((-8, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - 14, ASSEMBLY_HEAD_Z + CAMERA_Z)),
            COLORS["privacy"],
        ),
    ]
    render(exploded, RENDERS / "jeli-exploded.png", camera=(255, -300, 230))

    proxies = component_proxies()
    component_scene = [
        RenderItem(base_bottom.translate((0, 0, BASE[2] / 2)), COLORS["rear"]),
        RenderItem(yoke.translate((0, ASSEMBLY_HEAD_Y, BASE[2])), (28, 48, 42)),
        RenderItem(head_rear.translate((0, ASSEMBLY_HEAD_Y, ASSEMBLY_HEAD_Z)), COLORS["rear"]),
        RenderItem(
            bezel.translate((0, ASSEMBLY_HEAD_Y - HEAD[1] / 2 - 1, ASSEMBLY_HEAD_Z + DISPLAY_Z)),
            COLORS["accent"],
        ),
    ]
    for name in ("display", "camera", "speaker"):
        component_scene.append(
            RenderItem(proxies[name].translate((0, ASSEMBLY_HEAD_Y, ASSEMBLY_HEAD_Z)), COLORS["component"])
        )
    component_scene.extend(
        [
            RenderItem(proxies["nfc"].translate((0, 0, BASE[2] / 2)), COLORS["nfc"]),
            RenderItem(proxies["servo"].translate((0, 0, BASE[2] / 2)), (35, 82, 176)),
            RenderItem(proxies["pi"].translate((0, 0, BASE[2] / 2)), (24, 130, 76)),
        ]
    )
    render(component_scene, RENDERS / "jeli-component-fit.png", camera=(255, -300, 230))

    accessory_scene = [
        RenderItem(power_tray.translate((35, 25, POWER_SLED[2] / 2)), COLORS["rear"]),
        RenderItem(proxies["power_bank"].translate((35, 25, POWER_BANK[2] / 2 + POWER_SLED[2])), (72, 72, 78)),
        RenderItem(pi_tray.translate((-78, 24, PI_CARRIER[2] / 2)), COLORS["shell"]),
        RenderItem(
            rounded_box(PI_BOARD, 1.5, (-78, 24, PI_CARRIER[2] + PI_STANDOFF_H + PI_BOARD[2] / 2)),
            (24, 130, 76),
        ),
        RenderItem(camera_tray.translate((-78, -48, ARDUCAM_CARRIER[2] / 2)), COLORS["accent"]),
        RenderItem(
            rounded_box((CAMERA_PCB[0], CAMERA_PCB[2], CAMERA_PCB[1]), 2, (-78, -48, ARDUCAM_CARRIER[2] + CAMERA_PCB[1] / 2)),
            (45, 45, 50),
        ),
    ]
    render(
        accessory_scene,
        RENDERS / "jeli-prototype-accessories.png",
        camera=(225, -280, 180),
        target=(-10, 0, 15),
    )

    manifest = {
        "generator": "manifold3d",
        "units": "millimetres",
        "parts": sorted(printable),
        "assembly_envelope_mm": [124, 114, 150],
        "source_contract": "jeli-config.scad",
    }
    (EXPORTS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    try:
        build()
    except Exception as error:
        print(f"Jeli generation failed: {error}", file=sys.stderr)
        raise
