import unittest
from app.services.cost_splitter import CostSplitter


class TestCostSplitter(unittest.TestCase):
    def test_cost_splitter_ton_km_proportions(self):
        total_cost = 15000.0  # ₹15,000 for truck journey
        shipments = [
            {"id": 1, "weight_kg": 2000.0, "distance_km": 300.0},  # 2 tons * 300 km = 600 ton-km
            {"id": 2, "weight_kg": 1000.0, "distance_km": 300.0},  # 1 ton * 300 km = 300 ton-km
        ]
        # Total ton-km = 900.
        # Shipper 1 pays 600/900 = 2/3 * 15000 = 10,000
        # Shipper 2 pays 300/900 = 1/3 * 15000 = 5,000

        results = CostSplitter.calculate_split(total_cost, shipments, split_method="ton_km")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["allocated_cost"], 10000.0)
        self.assertEqual(results[1]["allocated_cost"], 5000.0)
        self.assertEqual(results[0]["savings_vs_dedicated_trip"], 5000.0)
        self.assertEqual(results[1]["savings_vs_dedicated_trip"], 10000.0)


if __name__ == "__main__":
    unittest.main()