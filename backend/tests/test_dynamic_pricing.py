"""
Task 9: dynamic pricing. price = base x (demand x urgency x fill), kept between 0.85 and 1.50.
"""
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services import dynamic_pricing as dp

API = "/api/v1/engine"
client = TestClient(app)

# Shipment 2 (450 kg plumbing fittings, Hosur to Chennai, 334.7 km) on truck 1 (2,500 kg, ₹28/km)
SHIP2 = dict(shipment_km=334.65, weight_kg=450, volume_cbm=0.96,
             truck_max_weight_kg=2500, truck_max_volume_cbm=14, rate_per_km=28)


def price(**conditions):
    return dp.quote(**SHIP2, **conditions)


class TestDynamicPricing(unittest.TestCase):
    def test_base_price(self):
        q = price()
        self.assertEqual(q["space_share_pct"], 18.0)            # 450 / 2500
        self.assertAlmostEqual(q["base_price"], 334.65 * 28 * 0.18, places=1)
        self.assertEqual(q["multiplier"], 1.0)                  # half full, standard, no demand data
        self.assertEqual(q["price"], q["base_price"])

    def test_urgent_costs_more(self):
        normal, express, urgent = price()["price"], price(urgency="express")["price"], price(urgency="urgent")["price"]
        self.assertLess(normal, express)
        self.assertLess(express, urgent)
        self.assertEqual(price(urgency="urgent")["multiplier"], 1.3)

    def test_nearly_empty_truck_costs_more(self):
        self.assertGreater(price(truck_fill_pct=5)["price"], price(truck_fill_pct=50)["price"])
        self.assertEqual(price(truck_fill_pct=0)["multiplier"], 1.15)

    def test_nearly_full_truck_costs_more(self):
        self.assertGreater(price(truck_fill_pct=95)["price"], price(truck_fill_pct=50)["price"])
        self.assertEqual(price(truck_fill_pct=100)["multiplier"], 1.2)

    def test_middle_fill_is_normal(self):
        self.assertEqual(price(truck_fill_pct=30)["multiplier"], 1.0)
        self.assertEqual(price(truck_fill_pct=75)["multiplier"], 1.0)

    def test_busy_route_costs_more_quiet_route_less(self):
        busy = price(open_shipments_on_route=8, trucks_available_on_route=1)
        quiet = price(open_shipments_on_route=2, trucks_available_on_route=1)
        self.assertEqual(busy["factors"]["demand"]["factor"], 1.2)   # 8 per truck: 4 above normal x 5%
        self.assertEqual(quiet["factors"]["demand"]["factor"], 0.9)
        self.assertGreater(busy["price"], price()["price"])
        self.assertLess(quiet["price"], price()["price"])

    def test_never_above_the_maximum_or_below_the_minimum(self):
        top = price(urgency="urgent", truck_fill_pct=100, open_shipments_on_route=50, trucks_available_on_route=1)
        self.assertEqual(top["multiplier"], dp.MAX_MULTIPLIER)
        self.assertEqual(top["capped"], "at maximum")
        self.assertGreater(top["raw_multiplier"], dp.MAX_MULTIPLIER)
        low = price(open_shipments_on_route=0, trucks_available_on_route=5)
        self.assertEqual(low["multiplier"], dp.MIN_MULTIPLIER)
        self.assertEqual(low["capped"], "at minimum")
        for fill in range(0, 101, 5):
            for urgency in ("standard", "express", "urgent"):
                for demand in (0, 2, 4, 8, 40):
                    m = price(truck_fill_pct=fill, urgency=urgency, open_shipments_on_route=demand,
                              trucks_available_on_route=1)["multiplier"]
                    self.assertTrue(dp.MIN_MULTIPLIER <= m <= dp.MAX_MULTIPLIER)

    def test_urgency_from_deadline(self):
        # 334.7 km is about 7.4 h of driving
        self.assertEqual(price(hours_until_deadline=10)["factors"]["urgency"]["level"], "urgent")   # 2.6 h spare
        self.assertEqual(price(hours_until_deadline=20)["factors"]["urgency"]["level"], "express")  # 12.6 h spare
        self.assertEqual(price(hours_until_deadline=72)["factors"]["urgency"]["level"], "standard")


class TestPricingEndpoints(unittest.TestCase):
    def test_example(self):
        spec = client.get("/api/v1/openapi.json").json()
        ex = spec["paths"][f"{API}/price"]["post"]["requestBody"]["content"]["application/json"][
            "examples"]["sample"]["value"]
        res = client.post(f"{API}/price", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["base_price"], 1686.83)
        self.assertEqual(body["multiplier"], 1.404)   # urgent 1.30 x 85% full 1.08
        self.assertEqual(body["price"], 2368.31)

    def test_demo_scenarios(self):
        res = client.get(f"{API}/demo-price/2").json()
        by_name = {s["scenario"].split(":")[0].split(" (")[0]: s for s in res["scenarios"]}
        normal = by_name["Normal"]["price"]
        self.assertGreater(by_name["Urgent"]["price"], normal)
        self.assertGreater(by_name["Truck nearly empty"]["price"], normal)
        self.assertGreater(by_name["Truck nearly full"]["price"], normal)
        self.assertEqual(by_name["Everything at once"]["multiplier"], 1.5)

    def test_needs_a_distance(self):
        res = client.post(f"{API}/price", json={"shipment": {"id": 1, "weight_kg": 100},
                                                "truck": {"id": 1, "max_weight_kg": 1000, "max_volume_cbm": 10}})
        self.assertEqual(res.status_code, 422)
        res = client.post(f"{API}/price", json={"shipment": {"id": 1, "weight_kg": 100, "distance_km": 100},
                                                "truck": {"id": 1, "max_weight_kg": 1000, "max_volume_cbm": 10,
                                                          "rate_per_km": 30}})
        self.assertEqual(res.json()["base_price"], 300.0)   # 100 km x 30 x 10%


if __name__ == "__main__":
    unittest.main()
