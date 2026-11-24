"""
Task 5: fuel and CO2 for separate trucks versus the pooled truck.

Stated factors: 0.28 L of diesel per km, 2.68 kg CO2 per litre.
"""
import asyncio
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.carbon_calculator import CarbonCalculator

API = "/api/v1"
client = TestClient(app)  # not a context manager, so startup (Postgres table creation) is skipped


class TestCompareTrips(unittest.TestCase):
    def test_three_shippers_on_one_truck(self):
        # Alone they drive 413 + 380 + 150 = 943 km; the pooled truck drives 420 km
        r = CarbonCalculator.compare_trips([413, 380, 150], 420)
        self.assertEqual(r["num_shipments"], 3)
        self.assertEqual(r["baseline_truck_km"], 943.0)
        self.assertEqual(r["pooled_truck_km"], 420.0)
        self.assertEqual(r["km_avoided"], 523.0)
        self.assertEqual(r["baseline_diesel_litres"], 264.04)   # 943 x 0.28
        self.assertEqual(r["pooled_diesel_litres"], 117.6)      # 420 x 0.28
        self.assertEqual(r["diesel_saved_litres"], 146.44)
        self.assertEqual(r["baseline_co2_kg"], 707.63)          # 264.04 x 2.68
        self.assertEqual(r["pooled_co2_kg"], 315.17)
        self.assertEqual(r["co2_saved_kg"], 392.46)
        self.assertEqual(r["co2_reduction_percentage"], 55.5)
        self.assertEqual(r["fuel_saved_percentage"], 55.5)

    def test_saved_is_baseline_minus_pooled(self):
        r = CarbonCalculator.compare_trips([150.19, 130.08, 82.61, 76.71], 150.19)
        self.assertAlmostEqual(r["diesel_saved_litres"], r["baseline_diesel_litres"] - r["pooled_diesel_litres"], 2)
        self.assertAlmostEqual(r["co2_saved_kg"], r["baseline_co2_kg"] - r["pooled_co2_kg"], 2)

    def test_factors_are_stated(self):
        f = CarbonCalculator.compare_trips([100], 100)["emission_factors"]
        self.assertEqual(f["diesel_litres_per_km"], 0.28)
        self.assertEqual(f["kg_co2_per_litre_diesel"], 2.68)
        self.assertEqual(f["kg_co2_per_km"], 0.7504)
        self.assertEqual(CarbonCalculator.trip_emissions(100), {"km": 100.0, "diesel_litres": 28.0, "co2_kg": 75.04})

    def test_single_shipper_saves_nothing(self):
        r = CarbonCalculator.compare_trips([413], 413)
        self.assertEqual((r["co2_saved_kg"], r["diesel_saved_litres"], r["co2_reduction_percentage"]), (0, 0, 0))
        self.assertEqual(r["baseline_diesel_litres"], 115.64)

    def test_never_negative(self):
        # A long detour for short trips: pooling would burn more, so saved is 0, not negative
        r = CarbonCalculator.compare_trips([50, 50], 400)
        self.assertEqual(r["co2_saved_kg"], 0.0)
        self.assertEqual(r["co2_reduction_percentage"], 0.0)
        self.assertEqual(r["pooled_co2_kg"], 300.16)

    def test_empty_pool_is_all_zeros(self):
        r = CarbonCalculator.compare_trips([], 413)
        self.assertEqual(r["num_shipments"], 0)
        self.assertEqual((r["baseline_co2_kg"], r["pooled_co2_kg"], r["co2_saved_kg"]), (0, 0, 0))

    def test_route_only_shortcut_keeps_old_numbers(self):
        r = CarbonCalculator.calculate_savings(413, 4, detour_km=10)
        self.assertEqual((r["baseline_truck_km"], r["pooled_truck_km"], r["km_avoided"]), (1652.0, 423.0, 1229.0))
        self.assertEqual(r["diesel_saved_litres"], 344.12)
        self.assertEqual(r["co2_saved_kg"], 922.24)
        self.assertEqual(r["co2_reduction_percentage"], 74.4)


class TestCarbonEndpoints(unittest.TestCase):
    def test_compare_endpoint(self):
        res = client.post(f"{API}/engine/carbon/compare",
                          json={"separate_trip_km": [413, 380, 150], "pooled_truck_km": 420})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["co2_saved_kg"], 392.46)
        self.assertEqual(res.json()["emission_factors"]["kg_co2_per_litre_diesel"], 2.68)

    def test_compare_endpoint_bad_input(self):
        for body in ({"separate_trip_km": [], "pooled_truck_km": 420},
                     {"separate_trip_km": [100, -5], "pooled_truck_km": 420},
                     {"separate_trip_km": [100], "pooled_truck_km": -1}):
            with self.subTest(body=body):
                self.assertEqual(client.post(f"{API}/engine/carbon/compare", json=body).status_code, 422)

    def test_old_carbon_endpoint_now_shows_litres_and_factors(self):
        r = client.post(f"{API}/engine/carbon",
                        json={"pooled_route_distance_km": 413, "num_participants": 4, "detour_km": 10}).json()
        self.assertEqual((r["baseline_diesel_litres"], r["pooled_diesel_litres"]), (462.56, 118.44))
        self.assertIn("emission_factors", r)

    def test_demo_uses_each_shipments_own_trip(self):
        r = client.get(f"{API}/engine/demo/2").json()["carbon"]
        self.assertEqual(r["num_shipments"], 4)
        self.assertEqual(r["baseline_truck_km"], 439.6)  # 4 shipments' own trips, not 4 x the truck route
        self.assertEqual(r["co2_reduction_percentage"], 65.8)


class TestSavedPoolCarbon(unittest.TestCase):
    """GET /pools/{id}/carbon and /analytics/summary, on an in-memory database."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool
        from app.db.base import Base
        from app.db.session import get_db
        from app.models import Shipment, Truck, User

        cls.engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool,
                                         connect_args={"check_same_thread": False})
        Session = async_sessionmaker(cls.engine, expire_on_commit=False)
        when = datetime(2026, 12, 1, tzinfo=timezone.utc)

        async def setup():
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with Session() as db:
                db.add(User(id=1, email="s@example.com", hashed_password="x", full_name="Shipper"))
                # Sample truck 2 and shipments 7 to 10 (Mumbai to Pune)
                db.add(Truck(id=2, transporter_id=1, truck_type="Eicher 14 ft", registration_number="MH12",
                             max_weight_kg=4000, max_volume_cbm=22, origin_city="Mumbai",
                             origin_lat=19.076, origin_lng=72.8777, destination_city="Pune",
                             dest_lat=18.5204, dest_lng=73.8567, available_date=when, rate_per_km=32))
                for id, kg, lat, lng, dlat, dlng in [
                    (7, 900, 19.076, 72.8777, 18.5204, 73.8567),
                    (8, 700, 19.0330, 73.0297, 18.5204, 73.8567),
                    (9, 800, 18.7546, 73.4062, 18.5204, 73.8567),
                    (10, 400, 19.076, 72.8777, 18.7546, 73.4062),
                    (11, 100, 19.076, 72.8777, 18.5204, 73.8567),  # never pooled
                ]:
                    db.add(Shipment(id=id, shipper_id=1, title=f"S{id}", goods_type="general", weight_kg=kg,
                                    volume_cbm=1.0, origin_address="A", origin_lat=lat, origin_lng=lng,
                                    destination_address="B", dest_lat=dlat, dest_lng=dlng))
                await db.commit()

        asyncio.run(setup())

        async def override_db():
            async with Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_1_pool_carbon_matches_what_was_saved(self):
        pool = client.post(f"{API}/pools/", json={"truck_id": 2, "shipment_ids": [7, 8, 9, 10]}).json()
        res = client.get(f"{API}/pools/{pool['id']}/carbon")
        self.assertEqual(res.status_code, 200, res.text)
        r = res.json()
        self.assertEqual((r["pool_id"], r["truck_id"], r["num_shipments"]), (pool["id"], 2, 4))
        self.assertEqual([t["shipment_id"] for t in r["separate_trips"]], [7, 8, 9, 10])
        # baseline = the four separate trips added up
        self.assertAlmostEqual(sum(t["km"] for t in r["separate_trips"]), r["baseline_truck_km"], 1)
        self.assertGreater(r["baseline_diesel_litres"], r["pooled_diesel_litres"])
        self.assertGreater(r["co2_reduction_percentage"], 0)
        # same numbers as stored on the pool when it was created
        self.assertEqual(r["co2_saved_kg"], pool["co2_saved_kg"])
        self.assertEqual(r["diesel_saved_litres"], pool["diesel_saved_litres"])

    def test_2_summary_totals(self):
        s = client.get(f"{API}/analytics/summary").json()
        self.assertEqual(s["platform_metrics"]["total_pools"], 1)
        self.assertEqual(s["platform_metrics"]["total_shipments_pooled"], 4)  # shipment 11 is not pooled
        pool_co2 = client.get(f"{API}/pools/1/carbon").json()["co2_saved_kg"]
        self.assertEqual(s["environmental_impact"]["total_co2_saved_kg"], pool_co2)
        self.assertEqual(s["environmental_impact"]["emission_factors"]["diesel_litres_per_km"], 0.28)

    def test_3_empty_pool_and_missing_pool(self):
        empty = client.post(f"{API}/pools/", json={"truck_id": 2}).json()
        r = client.get(f"{API}/pools/{empty['id']}/carbon").json()
        self.assertEqual((r["num_shipments"], r["co2_saved_kg"], r["separate_trips"]), (0, 0.0, []))
        self.assertEqual(client.get(f"{API}/pools/999/carbon").status_code, 404)


if __name__ == "__main__":
    unittest.main()
