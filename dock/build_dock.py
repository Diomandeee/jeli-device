#!/usr/bin/env python3
"""Adjustable dock that holds a cased Raspberry Pi beside Jeli (mm).

Reads dimensions from design.json, builds each part with manifold3d, checks
that the sliding stop clears the base across its whole travel, and writes one
STL per part to stl/.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from manifold3d import Manifold

CAD = Path(__file__).resolve().parent


def box(size, at):
    return Manifold.cube(size, center=True).translate(at)


def hole(d, h, x, y):
    return Manifold.cylinder(h, d/2, circular_segments=48, center=True).translate((x,y,0))


def slot(x1, x2, y, d, h=40):
    return Manifold.batch_hull([hole(d,h,x1,y), hole(d,h,x2,y)])


def geometry(c):
    bx, by, t = c['base_mm']
    support = c['support_height_above_plate']
    lip = c['stop_height_above_support']
    fixed = c['fixed_stop_inner_x']
    lo, hi = c['moving_stop_inner_x_range']
    gap = c['side_guide_inner_gap']
    d = c['bolt_clearance_diameter']
    base = box((bx,by,t),(0,0,t/2))
    base += box((4,gap,support+lip),(fixed-2,0,t+(support+lip)/2))
    # Rails stop before the entire swept volume of the sliding stop's foot.
    rail_min, rail_max = fixed+2, lo-15
    for y in (-30,30):
        base += box((rail_max-rail_min,8,support),
                    ((rail_max+rail_min)/2,y,t+support/2))
    for x in (-50,20):
        for y in (-gap/2-2,gap/2+2):
            base += box((10,4,support+lip),(x,y,t+(support+lip)/2))
    for x in (-43,-25,-7,11):
        base -= box((10,44,40),(x,0,0))
    for x in c['strap_x_positions']:
        for y in c['strap_y_positions']:
            base -= box((*c['strap_slot_mm'],40),(x,y,0))
    for y in (-47,47):
        base -= slot(lo-4,hi-4,y,d)
    # Local x=0 is the moving inner face; assembly shift is (x,0,t).
    stop = box((14,104,support),(-3,0,support/2))
    stop += box((4,gap,lip),(2,0,support+lip/2))
    for y in (-47,47):
        stop -= hole(d,40,-4,y)
    coupon = box((gap+6,22,2),(0,0,1))
    for x in (-gap/2-1.5,gap/2+1.5):
        coupon += box((3,22,8),(x,0,6))
    coupon -= box((*c['strap_slot_mm'],30),(-18,0,0))
    coupon -= hole(d,30,18,0)
    return {'dock_base':base,'sliding_end_stop':stop,'width_strap_bolt_coupon':coupon}


def mesh(solid):
    m=solid.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:,:3],np.asarray(m.tri_verts),process=True)


def build(out=CAD / 'stl'):
    c = json.loads((CAD / 'design.json').read_text())
    solids = geometry(c)
    lo, hi = c['moving_stop_inner_x_range']
    t = c['base_mm'][2]
    for x in np.linspace(lo, hi, 23):
        overlap = (solids['dock_base'] ^ solids['sliding_end_stop'].translate((float(x), 0, t))).volume()
        assert overlap < 1e-5, (x, overlap)
    out.mkdir(exist_ok=True)
    for name, solid in solids.items():
        path = out / f'{name}.stl'
        mesh(solid).export(path)
        m = trimesh.load_mesh(path)
        assert m.is_watertight and m.is_winding_consistent and m.volume > 0
        assert len(m.split()) == 1 and abs(m.bounds[0, 2]) < 1e-5
        print(f'{name}: {m.extents.round(1).tolist()} mm, {m.volume:.0f} mm3')


if __name__ == '__main__':
    build()
