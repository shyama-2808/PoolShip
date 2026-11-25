"""
Task 7: compatibility rules. Which goods can't share a truck, checked before pooling.
"""
import asyncio
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services import compatibility_rules as rules
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec

API = "/api/v1"
client = TestClient(app)  # not a context manager, so startup (Postgres table creation) is skipped

MANGOES = {"id": 3, "weight_kg": 500, "goods_type": "perishable", "is_perishable": True}
THINNER = {"id": 4, "weight_kg": 300, "goods_type": "chemicals", "is_hazardous": True}
SAREES = {"id": 1, "weight_kg": 600, "goods_type": "textiles"}


def item(id, goods_type=None, **flags):
    return ShipmentItem(id=id, weight_kg=100, volume_cbm=0.5, length_cm=100, width_cm=100, height_cm=50,
                        goods_type=goods_type, **flags)


class TestRuleTable(unittest.TestCase):
    def test_perishables_plus_chemicals_pool_is_rejected_with_a_reason(self):
        res = rules.check_pool([MANGOES, THINNER, SAREES])
        self.assertFalse(res["compatible"])
        self.assertEqual(res["reason"],
                         "Shipments 3 and 4 can't share a truck. Perishable food cannot be pooled with "
                         "hazardous chemicals: chemical leaks or fumes can spoil food")
        self.assertEqual(len(res["conflicts"]), 1)
        self.assertEqual(res["conflicts"][0]["shipment_ids"], [3, 4])

    def test_goods_type_alone_is_enough(self):
        # No flags set: the goods_type words still put them in the food and chemicals groups
        self.assertFalse(rules.check_pool([{"id": 1, "goods_type": "grains"},
                                           {"id": 2, "goods_type": "Chemicals"}])["compatible"])
        self.assertFalse(rules.check_pool([{"id": 1, "goods_type": "pharmaceuticals"},
                                           {"id": 2, "goods_type": "pesticides"}])["compatible"])

    def test_flags_alone_are_enough(self):
        self.assertFalse(rules.check_pool([{"id": 1, "is_perishable": True},
                                           {"id": 2, "is_hazardous": True}])["compatible"])

    def test_safe_mix_is_fine(self):
        res = rules.check_pool([SAREES, {"id": 2, "goods_type": "hardware"}, MANGOES])
        self.assertTrue(res["compatible"])
        self.assertEqual(res["reason"], "All shipments can share a truck")

    def test_chilled_and_frozen_cannot_share(self):
        res = rules.check_pool([{"id": 1, "goods_type": "dairy", "temperature_class": "chilled"},
                                {"id": 2, "goods_type": "perishable", "temperature_class": "frozen"}])
        self.assertFalse(res["compatible"])
        self.assertIn("Temperature mismatch", res["reason"])
        # Two frozen shipments are fine
        self.assertTrue(rules.check_pool([{"id": 1, "temperature_class": "frozen"},
                                          {"id": 2, "temperature_class": "frozen"}])["compatible"])

    def test_temperature_controlled_cannot_ride_with_chemicals(self):
        res = rules.check_pool([{"id": 1, "goods_type": "textiles", "temperature_class": "chilled"}, THINNER])
        self.assertFalse(res["compatible"])
        self.assertIn("refrigerated hold", res["reason"])

    def test_fragile_with_construction_is_a_caution_not_a_block(self):
        res = rules.check_pool([{"id": 15, "goods_type": "textiles", "is_fragile": True},
                                {"id": 16, "goods_type": "construction"}])
        self.assertTrue(res["compatible"])
        self.assertEqual(len(res["cautions"]), 1)
        self.assertIn("crush fragile goods", res["cautions"][0]["reason"])

    def test_flags_give_handling_notes(self):
        res = rules.check_pool([{"id": 9, "goods_type": "glassware"},
                                {"id": 10, "goods_type": "perishable", "temperature_class": "frozen"}])
        flags = {f["shipment_id"]: f["flags"] for f in res["flags"]}
        self.assertEqual(flags, {9: ["fragile"], 10: ["frozen"]})

    def test_packing_uses_the_rules(self):
        truck = TruckSpec(id=1, max_weight_kg=5000, max_volume_cbm=20, length_cm=400, width_cm=200, height_cm=200)
        res = CapacityOptimizer.optimize_load(truck, [item(1, "grains"), item(2, "chemicals")])
        self.assertEqual(len(res["unpacked_items"]), 1)
        self.assertIn("cannot be pooled with", res["unpacked_items"][0]["reason"])


class TestCompatibilityEndpoints(unittest.TestCase):
    def test_pool_check_endpoint_rejects_food_with_chemicals(self):
        spec = client.get(f"{API}/openapi.json").json()
        ex = spec["paths"][f"{API}/engine/compatibility/pool"]["post"]["requestBody"]["content"][
            "application/json"]["examples"]["sample"]["value"]
        res = client.post(f"{API}/engine/compatibility/pool", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertFalse(body["compatible"])
        self.assertEqual(body["conflicts"][0]["shipment_ids"], [3, 4])
        self.assertIn("chemical leaks or fumes can spoil food", body["reason"])

    def test_pair_endpoint_names_the_clashing_shipment(self):
        res = client.post(f"{API}/engine/compatibility",
                          json={"existing_items": [MANGOES], "candidate": THINNER}).json()
        self.assertFalse(res["compatible"])
        self.assertIn("clashes with shipment 3", res["reason"])

    def test_rules_endpoint(self):
        res = client.get(f"{API}/engine/compatibility/rules").json()
        pairs = {(r["group_a"], r["group_b"]) for r in res["rules"]}
        self.assertIn(("perishable", "hazardous"), pairs)
        self.assertIn(("chilled", "frozen"), pairs)

    def test_bad_temperature_class_is_422(self):
        res = client.post(f"{API}/engine/compatibility/pool",
                          json={"shipments": [{"id": 1, "weight_kg": 5, "temperature_class": "warm"}]})
        self.assertEqual(res.status_code, 422)


try:
    import aiosqlite  # noqa: F401
    HAVE_SQLITE = True
except ImportError:
    HAVE_SQLITE = False


@unittest.skipUnless(HAVE_SQLITE, "pip install aiosqlite to run the POST /pools tests")
class TestCreatePoolChecksCompatibility(unittest.TestCase):
    """POST /pools refuses perishables + chemicals before saving anything."""

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

        async def setup():
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with Session() as db:
                db.add(User(id=1, email="s@example.com", hashed_password="x", full_name="Shipper"))
                db.add(Truck(id=1, transporter_id=1, truck_type="Tata 407", registration_number="KA01",
                             max_weight_kg=2500, max_volume_cbm=14, origin_city="Bengaluru",
                             origin_lat=12.9716, origin_lng=77.5946, destination_city="Chennai",
                             dest_lat=13.0827, dest_lng=80.2707,
                             available_date=datetime(2026, 12, 1, tzinfo=timezone.utc), rate_per_km=28))
                for id, goods, perishable, hazardous in [(1, "perishable", True, False),
                                                         (2, "chemicals", False, True),
                                                         (3, "textiles", False, False)]:
                    db.add(Shipment(id=id, shipper_id=1, title=f"S{id}", goods_type=goods, weight_kg=300,
                                    volume_cbm=1, is_perishable=perishable, is_hazardous=hazardous,
                                    origin_address="Bengaluru", origin_lat=12.9716, origin_lng=77.5946,
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

    def test_1_food_and_chemicals_pool_is_refused(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [1, 2, 3]})
        self.assertEqual(res.status_code, 422, res.text)
        detail = res.json()["detail"]
        self.assertIn("Shipments 1 and 2 can't share a truck", detail["message"])
        self.assertEqual(detail["conflicts"][0]["shipment_ids"], [1, 2])

    def test_2_nothing_was_saved_so_a_safe_pool_still_works(self):
        res = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [1, 3]})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["shipments"][0]["temperature_class"], "ambient")


if __name__ == "__main__":
    unittest.main()
