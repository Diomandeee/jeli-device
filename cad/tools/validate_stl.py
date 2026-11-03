#!/usr/bin/env python3
"""Validate STL triangle topology using only the Python standard library."""

from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path


def read_binary(data: bytes):
    count = struct.unpack_from("<I", data, 80)[0]
    if 84 + count * 50 != len(data):
        return None
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        triangles.append((values[3:6], values[6:9], values[9:12]))
        offset += 50
    return triangles


def read_ascii(data: bytes):
    vertices = []
    for raw in data.decode("utf-8", errors="ignore").splitlines():
        fields = raw.strip().split()
        if len(fields) == 4 and fields[0] == "vertex":
            vertices.append(tuple(float(value) for value in fields[1:]))
    if len(vertices) % 3:
        raise ValueError("ASCII STL has an incomplete triangle")
    return [tuple(vertices[index : index + 3]) for index in range(0, len(vertices), 3)]


def quantize(vertex, precision=1e-5):
    return tuple(round(value / precision) for value in vertex)


def signed_volume(triangle):
    a, b, c = triangle
    cross = (
        b[1] * c[2] - b[2] * c[1],
        b[2] * c[0] - b[0] * c[2],
        b[0] * c[1] - b[1] * c[0],
    )
    return (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6.0


def inspect(path: Path):
    data = path.read_bytes()
    triangles = read_binary(data) if len(data) >= 84 else None
    if triangles is None:
        triangles = read_ascii(data)

    edges = Counter()
    points = []
    volume = 0.0
    for triangle in triangles:
        keys = [quantize(vertex) for vertex in triangle]
        points.extend(triangle)
        volume += signed_volume(triangle)
        for start, end in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((keys[start], keys[end])))] += 1

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    boundary = sum(count == 1 for count in edges.values())
    nonmanifold = sum(count > 2 for count in edges.values())
    return {
        "file": path.name,
        "triangles": len(triangles),
        "bounds_mm": {
            "min": [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
            "max": [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
            "size": [
                round(max(xs) - min(xs), 3),
                round(max(ys) - min(ys), 3),
                round(max(zs) - min(zs), 3),
            ],
        },
        "volume_mm3": round(abs(volume), 2),
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "watertight": boundary == 0 and nonmanifold == 0 and not math.isclose(volume, 0.0),
    }


def main(argv):
    if not argv:
        raise SystemExit("usage: validate_stl.py FILE.stl [...]")
    records = [inspect(Path(value)) for value in argv]
    print(json.dumps({"parts": records, "all_watertight": all(r["watertight"] for r in records)}, indent=2))
    return 0 if all(record["watertight"] for record in records) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

