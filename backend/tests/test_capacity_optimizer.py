import unittest
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec


class TestCapacityOptimizer(unittest.TestCase):
    def test_capacity_optimizer_weight_and_volume_fit(self):
        truck = TruckSpec(
            id=1,
            max_weight_kg=2500.0,
            max_volume_cbm=12.0,
            length_cm=400.0,
            width_cm=200.0,
            height_cm=200.0,
        )

        items = [
            ShipmentItem(id=1, weight_kg=800.0, volume_cbm=3.5, length_cm=150, width_cm=100, height_cm=100),
            ShipmentItem(id=2, weight_kg=1200.0, volume_cbm=4.0, length_cm=180, width_cm=100, height_cm=120),
            ShipmentItem(id=3, weight_kg=900.0, volume_cbm=5.0, length_cm=200, width_cm=150, height_cm=100),  # Should not fit in weight
        ]

        result = CapacityOptimizer.optimize_load(truck, items)

        self.assertEqual(len(result["packed_items"]), 2)
        self.assertEqual(len(result["unpacked_items"]), 1)
        self.assertEqual(result["total_packed_weight_kg"], 2000.0)
        self.assertEqual(result["unpacked_items"][0]["reason"], "Exceeds truck weight capacity")

    def test_capacity_optimizer_hazardous_compatibility(self):
        truck = TruckSpec(id=1, max_weight_kg=5000.0, max_volume_cbm=20.0, length_cm=500, width_cm=200, height_cm=200)

        items = [
            ShipmentItem(id=1, weight_kg=500.0, volume_cbm=2.0, length_cm=100, width_cm=100, height_cm=100, is_perishable=True),
            ShipmentItem(id=2, weight_kg=500.0, volume_cbm=2.0, length_cm=100, width_cm=100, height_cm=100, is_hazardous=True),
        ]

        result = CapacityOptimizer.optimize_load(truck, items)
        self.assertEqual(len(result["packed_items"]), 1)
        self.assertEqual(len(result["unpacked_items"]), 1)
        self.assertIn("cannot be pooled with", result["unpacked_items"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
