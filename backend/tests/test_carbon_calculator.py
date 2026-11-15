import unittest
from app.services.carbon_calculator import CarbonCalculator


class TestCarbonCalculator(unittest.TestCase):
    def test_carbon_calculator_savings(self):
        savings = CarbonCalculator.calculate_savings(
            pooled_route_distance_km=300.0,
            num_participants=3,
            detour_km=20.0
        )

        self.assertEqual(savings["baseline_truck_km"], 900.0)
        self.assertEqual(savings["pooled_truck_km"], 320.0)
        self.assertEqual(savings["km_avoided"], 580.0)
        self.assertGreater(savings["diesel_saved_litres"], 0)
        self.assertGreater(savings["co2_saved_kg"], 0)


if __name__ == "__main__":
    unittest.main()
