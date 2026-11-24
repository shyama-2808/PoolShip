"""
Task 3 (truck capacity: spread a pool over trucks) and Task 4 (cost split that adds up
to the paisa), plus POST /pools saving the shipments and their shares.
"""
import asyncio
import random
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec
from app.services.cost_splitter import SPLIT_METHODS, CostSplitter, to_paise

API = "/api/v1"
client = TestClient(app)  # not a context manager, so startup (Postgres table creation) is skipped


def item(id, kg, cbm, size=(100, 100, 100), **flags):
    return ShipmentItem(id=id, weight_kg=kg, volume_cbm=cbm, length_cm=size[0], width_cm=size[1],
                        height_cm=size[2], **flags)


def truck(id, kg, cbm):
    return TruckSpec(id=id, max_weight_kg=kg, max_volume_cbm=cbm, length_cm=430, width_cm=200, height_cm=200)


class TestCostSplitAddsUp(unittest.TestCase):
    def test_trip_cost_from_distance(self):
        self.assertEqual(CostSplitter.trip_cost(413.3, 28), 11572.4)
        self.assertEqual(CostSplitter.trip_cost(0.0001, 35), 0.0)

    def test_three_way_split_of_100_rupees(self):
        res = CostSplitter.calculate_split(100, [{"id": i, "weight_kg": 1} for i in (1, 2, 3)], "weight")
        self.assertEqual([r["allocated_paise"] for r in res], [3334, 3333, 3333])
        self.assertEqual(sum(r["allocated_paise"] for r in res), 10000)

    def test_distance_method(self):
        res = CostSplitter.calculate_split(
            900, [{"id": 1, "weight_kg": 999, "distance_km": 200}, {"id": 2, "weight_kg": 1, "distance_km": 100}],
            "distance")
        self.assertEqual([r["allocated_cost"] for r in res], [600.0, 300.0])

    def test_every_method_adds_up_exactly_on_random_pools(self):
        rng = random.Random(7)
        for _ in range(500):
            total = round(rng.uniform(1, 50000), 2)
            ships = [{"id": i, "weight_kg": round(rng.uniform(1, 3000), 1),
                      "volume_cbm": round(rng.uniform(0.01, 10), 3),
                      "distance_km": round(rng.uniform(1, 900), 1)} for i in range(rng.randint(1, 9))]
            for method in SPLIT_METHODS:
                res = CostSplitter.calculate_split(total, ships, method)
                self.assertEqual(sum(r["allocated_paise"] for r in res), to_paise(total), (total, method))
                self.assertTrue(all(r["allocated_paise"] >= 0 for r in res))

    def test_nothing_to_go_on_splits_equally(self):
        res = CostSplitter.calculate_split(10, [{"id": i, "weight_kg": 1, "volume_cbm": 0} for i in (1, 2, 3)],
                                           "volume")
        self.assertEqual(sum(r["allocated_paise"] for r in res), 1000)
        self.assertEqual(max(r["allocated_paise"] for r in res) - min(r["allocated_paise"] for r in res), 1)

    def test_api_works_out_cost_from_distance_and_rate(self):
        body = {"trip_distance_km": 413.3, "rate_per_km": 28, "split_method": "distance",
                "shipments": [{"id": 1, "weight_kg": 600, "distance_km": 413},
                              {"id": 2, "weight_kg": 450, "distance_km": 340},
                              {"id": 5, "weight_kg": 350, "distance_km": 160}]}
        res = client.post(f"{API}/engine/cost-split", json=body).json()
        self.assertEqual(res["total_trip_cost"], 11572.4)
        self.assertEqual(sum(s["allocated_paise"] for s in res["shares"]), 1157240)

    def test_api_needs_a_cost(self):
        res = client.post(f"{API}/engine/cost-split", json={"shipments": [{"id": 1, "weight_kg": 5}]})
        self.assertEqual(res.status_code, 422)


class TestAssignToTrucks(unittest.TestCase):
    def test_biggest_first_into_first_truck_with_room(self):
        res = CapacityOptimizer.assign_to_trucks(
            [truck(1, 1000, 10), truck(2, 1000, 10)],
            [item(1, 300, 1), item(2, 700, 1), item(3, 600, 1), item(4, 400, 1)])
        self.assertEqual([t["shipment_ids"] for t in res["trucks"]], [[2, 1], [3, 4]])
        self.assertEqual([t["overall_utilization_pct"] for t in res["trucks"]], [100.0, 100.0])
        self.assertEqual(res["leftover_items"], [])
        self.assertEqual(res["trucks_used"], 2)

    def test_bulky_light_item_counts_as_big(self):
        res = CapacityOptimizer.assign_to_trucks([truck(1, 1000, 10)], [item(1, 900, 1), item(2, 50, 9.5)])
        # foam (2) goes first because it fills 95% of the volume; then the 900 kg crate can't fit by volume
        self.assertEqual(res["trucks"][0]["shipment_ids"], [2])
        self.assertIn("volume", res["leftover_items"][0]["reason"])

    def test_leftovers_say_why(self):
        res = CapacityOptimizer.assign_to_trucks(
            [truck(1, 500, 5)], [item(1, 400, 1), item(2, 300, 1), item(3, 900, 1)])
        reasons = {u["item"].id: u["reason"] for u in res["leftover_items"]}
        self.assertTrue(reasons[3].startswith("Too big for every truck"))
        self.assertTrue(reasons[2].startswith("No truck has room left"))

    def test_food_and_chemicals_go_in_different_trucks(self):
        res = CapacityOptimizer.assign_to_trucks(
            [truck(1, 5000, 20), truck(2, 5000, 20)],
            [item(1, 500, 1, is_perishable=True), item(2, 400, 1, is_hazardous=True)])
        self.assertEqual([t["shipment_ids"] for t in res["trucks"]], [[1], [2]])

    def test_no_truck_is_ever_overloaded(self):
        rng = random.Random(11)
        for _ in range(300):
            trucks = [truck(i, rng.choice([1500, 2500, 4000, 7000]), rng.choice([8, 14, 22, 32]))
                      for i in range(1, rng.randint(1, 4) + 1)]
            ships = [item(i, round(rng.uniform(50, 3000), 1), round(rng.uniform(0.1, 8), 2),
                          is_perishable=rng.random() < 0.15, is_hazardous=rng.random() < 0.1)
                     for i in range(1, rng.randint(1, 15) + 1)]
            res = CapacityOptimizer.assign_to_trucks(trucks, ships)
            seen = []
            for t, spec in zip(res["trucks"], trucks):
                kg = sum(i.weight_kg for i in t["packed_items"])
                cbm = sum(i.volume_cbm for i in t["packed_items"])
                self.assertLessEqual(kg, spec.max_weight_kg + 1e-6)
                self.assertLessEqual(cbm, spec.max_volume_cbm + 1e-6)
                self.assertLessEqual(t["overall_utilization_pct"], 100.0)
                seen += t["shipment_ids"]
            seen += [u["item"].id for u in res["leftover_items"]]
            self.assertEqual(sorted(seen), [s.id for s in ships])  # each shipment exactly once

    def test_api_example_splits_bengaluru_chennai_pool(self):
        spec = client.get(f"{API}/openapi.json").json()
        ex = spec["paths"][f"{API}/engine/assign-trucks"]["post"]["requestBody"]["content"][
            "application/json"]["examples"]["sample"]["value"]
        res = client.post(f"{API}/engine/assign-trucks", json=ex).json()
        loads = {t["truck_id"]: set(t["shipment_ids"]) for t in res["trucks"]}
        self.assertEqual(loads[1] | loads[5], {1, 2, 3, 4, 5, 6})
        self.assertFalse({3, 4} <= loads[1] or {3, 4} <= loads[5])  # mangoes and paint thinner apart
        self.assertEqual(res["leftover_items"], [])


try:
    import aiosqlite  # noqa: F401
    HAVE_SQLITE = True
except ImportError:
    HAVE_SQLITE = False


@unittest.skipUnless(HAVE_SQLITE, "pip install aiosqlite to run the POST /pools tests")
class TestCreatePoolSavesShipments(unittest.TestCase):
    """POST /pools against a throwaway in-memory database."""

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
                db.add(Truck(id=1, transporter_id=1, truck_type="Tata 407", registration_number="KA01",
                             max_weight_kg=2500, max_volume_cbm=14, origin_city="Bengaluru",
                             origin_lat=12.9716, origin_lng=77.5946, destination_city="Chennai",
                             dest_lat=13.0827, dest_lng=80.2707, available_date=when, rate_per_km=28))
                for id, kg, cbm, lat, lng in [(1, 600, 1.8, 12.9716, 77.5946), (2, 450, 0.96, 12.7409, 77.8253),
                                              (3, 350, 0.99, 12.9165, 79.1325), (4, 2400, 2.0, 12.9716, 77.5946),
                                              (5, 300, 0.5, 12.9716, 77.5946)]:
                    db.add(Shipment(id=id, shipper_id=1, title=f"S{id}", goods_type="general", weight_kg=kg,
                                    volume_cbm=cbm, origin_address="A", origin_lat=lat, origin_lng=lng,
                                    destination_address="Chennai", dest_lat=13.0827, dest_lng=80.2707))
                await db.commit()

        asyncio.run(setup())

        async def override_db():
            async with Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_1_create_pool_attaches_shipments_and_saves_shares(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [1, 2, 3],
                                                 "split_method": "weight"})
        self.assertEqual(res.status_code, 200, res.text)
        pool = res.json()
        self.assertEqual(pool["status"], "OPTIMIZED")
        self.assertEqual(pool["split_method"], "weight")
        self.assertEqual(pool["current_weight_kg"], 1400)
        self.assertEqual(pool["utilization_percentage"], 56.0)
        self.assertGreater(pool["co2_saved_kg"], 0)
        ships = {s["id"]: s for s in pool["shipments"]}
        self.assertEqual(set(ships), {1, 2, 3})
        self.assertTrue(all(s["status"] == "POOLED" and s["pool_id"] == pool["id"] for s in ships.values()))
        self.assertEqual(sum(to_paise(s["allocated_cost"]) for s in ships.values()), to_paise(pool["total_cost"]))
        self.assertGreater(ships[1]["allocated_cost"], ships[3]["allocated_cost"])  # heavier pays more

        again = client.get(f"{API}/pools/{pool['id']}").json()
        self.assertEqual(len(again["shipments"]), 3)

    def test_2_shipment_cannot_join_two_pools(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [1]})
        self.assertEqual(res.status_code, 409)

    def test_3_overload_is_refused_and_nothing_saved(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [4, 5]})  # 2,700 kg > 2,500
        self.assertEqual(res.status_code, 422)
        self.assertIn("weight", res.json()["detail"]["does_not_fit"][0]["reason"])
        # nothing was saved, so shipment 4 on its own can still be pooled
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [4], "split_method": "volume"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["shipments"][0]["allocated_cost"], res.json()["total_cost"])

    def test_4_bad_input(self):
        self.assertEqual(client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [99]}).status_code, 404)
        self.assertEqual(client.post(f"{API}/pools/", json={"truck_id": 9, "shipment_ids": [5]}).status_code, 404)
        self.assertEqual(client.post(f"{API}/pools/", json={"truck_id": 1, "split_method": "magic"}).status_code, 422)

    def test_5_empty_pool_still_allowed(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "OPEN")


if __name__ == "__main__":
    unittest.main()
