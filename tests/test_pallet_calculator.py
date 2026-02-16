import unittest

from pallet_calculator import DEFAULT_CARTONS, PALLETS, calculate_plan, parse_items


class PalletCalculatorTests(unittest.TestCase):
    def test_parse_items(self):
        parsed = parse_items(["KARTON L=2", "KARTON GAIA=3", "KARTON L=1"])
        self.assertEqual(parsed["KARTON L"], 3)
        self.assertEqual(parsed["KARTON GAIA"], 3)

    def test_calculate_simple_height(self):
        plan = calculate_plan(
            DEFAULT_CARTONS,
            PALLETS["80x120"],
            {"KARTON L": 2},
            pallet_base_height_cm=14,
        )
        self.assertEqual(plan["layers_count"], 1)
        self.assertEqual(plan["total_height_cm"], 41)

    def test_missing_weight_marks_incomplete(self):
        plan = calculate_plan(
            DEFAULT_CARTONS,
            PALLETS["80x120"],
            {"KARTON L": 1, "KARTON GAIA": 1},
        )
        self.assertFalse(plan["weight_complete"])
        self.assertIsNone(plan["total_weight_kg"])


if __name__ == "__main__":
    unittest.main()
