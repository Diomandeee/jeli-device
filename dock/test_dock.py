"""Geometric checks, not a substitute for a physical fit and slicer review."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_dock as dock


class DockGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((dock.CAD/'design.json').read_text())
        cls.s=dock.geometry(cls.c)

    def test_closed_single_solid_parts(self):
        for name,solid in self.s.items():
            with self.subTest(name=name):
                m=dock.mesh(solid)
                self.assertTrue(m.is_watertight)
                self.assertTrue(m.is_winding_consistent)
                self.assertEqual(len(m.split()),1)
                self.assertGreater(m.volume,0)

    def test_both_reported_case_lengths_clear_at_support_height(self):
        for length in (101.6,114.3,120):
            with self.subTest(length=length):
                minimum=self.c['fixed_stop_inner_x']+1
                proxy=dock.box((length,76.2,38.1),(minimum+length/2,0,7.2+38.1/2))
                stop=self.s['sliding_end_stop'].translate((minimum+length+1,0,3.2))
                self.assertLess(abs((proxy ^ self.s['dock_base']).volume()),1e-5)
                self.assertLess(abs((proxy ^ stop).volume()),1e-5)

    def test_full_stop_travel_has_no_base_collision(self):
        for x in range(40,63):
            moving=self.s['sliding_end_stop'].translate((x,0,3.2))
            self.assertLess(abs((moving ^ self.s['dock_base']).volume()),1e-5)

    def test_wrong_stop_position_is_detected(self):
        moving=self.s['sliding_end_stop'].translate((20,0,3.2))
        self.assertGreater((moving ^ self.s['dock_base']).volume(),1)

    def test_bolt_paths_are_clear_at_both_extremes(self):
        for x in (40,62):
            moving=self.s['sliding_end_stop'].translate((x,0,3.2))
            for y in (-47,47):
                bolt=dock.hole(3.0,40,x-4,y)
                self.assertLess(abs((bolt ^ (moving+self.s['dock_base'])).volume()),1e-5)

    def test_coupon_rejects_overwide_case(self):
        fits=dock.box((87,10,4),(0,0,5))
        too_wide=dock.box((90,10,4),(0,0,5))
        self.assertLess(abs((fits ^ self.s['width_strap_bolt_coupon']).volume()),1e-5)
        self.assertGreater((too_wide ^ self.s['width_strap_bolt_coupon']).volume(),1)


if __name__=='__main__':unittest.main()
