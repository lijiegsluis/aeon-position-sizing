import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main as ps  # noqa: E402


def fixed(**over):
    inputs = {"capital": 100000, "risk_pct": 0.01, "entry": 100, "stop": 95, "target": 115, "conviction": 7}
    inputs.update(over)
    return ps.run_fixed_risk(inputs, silent=True)


class Kelly(unittest.TestCase):
    def test_formula(self):
        self.assertAlmostEqual(ps.kelly_fraction(0.6, 2.5), (0.6 * 2.5 - 0.4) / 2.5, places=12)
        self.assertLess(ps.kelly_fraction(0.3, 1.0), 0)

    def test_cap_and_negative_edge(self):
        r = ps.run_kelly({"p": 0.6, "b": 2.5, "capital": 100000, "max_cap": 0.10}, silent=True)
        self.assertEqual(r["full_kelly"], 0.10)
        r = ps.run_kelly({"p": 0.3, "b": 1.0, "capital": 100000, "max_cap": 0.10}, silent=True)
        self.assertEqual((r["full_kelly"], r["half_kelly"]), (0.0, 0.0))


class FixedRisk(unittest.TestCase):
    def test_standard_case(self):
        r = fixed()
        self.assertEqual(r["shares"], 200)
        self.assertAlmostEqual(r["r_multiple"], 3.0, places=12)
        self.assertAlmostEqual(r["risk_dollars"], 1000.0, places=9)

    def test_tight_stop_never_exceeds_capital(self):
        r = fixed(stop=99.99, target=110)
        self.assertLessEqual(r["position_value"], 100000)
        self.assertEqual(r["shares"], 1000)

    def test_short_r_multiple(self):
        self.assertAlmostEqual(fixed(entry=100, stop=105, target=85)["r_multiple"], 3.0, places=12)


class Conviction(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(ps.conviction_tier(9)[1:], (0.5, 0.08))
        self.assertEqual(ps.conviction_tier(6)[1:], (0.25, 0.05))
        self.assertEqual(ps.conviction_tier(2)[1:], (None, 0.02))

    def test_never_negative(self):
        r = ps.run_conviction({"p": 0.3, "b": 1.0, "capital": 100000, "conviction": 9}, silent=True)
        self.assertEqual(r["final_alloc"], 0.0)

    def test_capped_at_tier_limit(self):
        r = ps.run_conviction({"p": 0.6, "b": 2.5, "capital": 100000, "conviction": 9}, silent=True)
        self.assertEqual(r["final_alloc"], 0.08)


if __name__ == "__main__":
    unittest.main()
