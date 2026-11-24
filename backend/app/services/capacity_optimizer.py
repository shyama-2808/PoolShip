from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services import compatibility_rules


# Small allowance so 2500.0000001 kg of float maths still counts as 2500 kg
_EPS = 1e-9


@dataclass
class ShipmentItem:
    id: int
    weight_kg: float
    volume_cbm: float
    length_cm: float
    width_cm: float
    height_cm: float
    is_perishable: bool = False
    is_hazardous: bool = False
    is_fragile: bool = False
    goods_type: Optional[str] = None          # e.g. "chemicals", "perishable" (see compatibility_rules)
    temperature_class: str = "ambient"        # "ambient", "chilled" or "frozen"


@dataclass
class TruckSpec:
    id: int
    max_weight_kg: float
    max_volume_cbm: float
    length_cm: float
    width_cm: float
    height_cm: float


class CapacityOptimizer:
    """
    Load consolidation & Bin-packing engine for PoolShip trucks.
    Validates dimensional fit, weight constraints, and cargo compatibility rules.
    """

    @staticmethod
    def check_compatibility(existing_items: List[ShipmentItem], candidate: ShipmentItem) -> Tuple[bool, str]:
        """
        Can `candidate` share a truck with `existing_items`?
        Uses the rule table in compatibility_rules.py (e.g. food never rides with chemicals,
        chilled and frozen goods never share a hold). Returns (ok, reason).
        """
        ok, reason, _cautions = compatibility_rules.check_candidate(existing_items, candidate)
        return ok, reason

    @staticmethod
    def item_volume(item: ShipmentItem) -> float:
        """Volume in m³; worked out from the dimensions if not given."""
        if item.volume_cbm and item.volume_cbm > 0:
            return item.volume_cbm
        return (item.length_cm * item.width_cm * item.height_cm) / 1_000_000.0

    @classmethod
    def why_not_fit(
        cls,
        truck: TruckSpec,
        loaded: List[ShipmentItem],
        loaded_weight: float,
        loaded_volume: float,
        item: ShipmentItem,
    ) -> Optional[str]:
        """None if the item can go in this truck on top of what is loaded, else the reason."""
        is_compat, reason = cls.check_compatibility(loaded, item)
        if not is_compat:
            return reason
        if loaded_weight + item.weight_kg > truck.max_weight_kg + _EPS:
            return "Exceeds truck weight capacity"
        if loaded_volume + cls.item_volume(item) > truck.max_volume_cbm + _EPS:
            return "Exceeds truck volume capacity"
        if (item.length_cm > truck.length_cm or
                item.width_cm > truck.width_cm or
                item.height_cm > truck.height_cm):
            return "Item dimensions exceed truck cargo hold dimensions"
        return None

    @staticmethod
    def _fill(truck: TruckSpec, weight: float, volume: float) -> Dict[str, float]:
        w = (weight / truck.max_weight_kg) * 100.0 if truck.max_weight_kg > 0 else 0.0
        v = (volume / truck.max_volume_cbm) * 100.0 if truck.max_volume_cbm > 0 else 0.0
        return {
            "weight_utilization_pct": round(w, 1),
            "volume_utilization_pct": round(v, 1),
            # A truck is as "full" as its tightest limit
            "overall_utilization_pct": round(max(w, v), 1),
        }

    @classmethod
    def optimize_load(
        cls,
        truck: TruckSpec,
        candidate_shipments: List[ShipmentItem]
    ) -> Dict[str, Any]:
        """
        Pack shipments into ONE truck (weight + volume + size + compatibility).
        Densest items go first; anything that doesn't fit comes back with the reason.
        """
        sorted_shipments = sorted(
            candidate_shipments,
            key=lambda x: (x.weight_kg / max(x.volume_cbm, 0.001)),
            reverse=True
        )

        packed: List[ShipmentItem] = []
        unpacked: List[Dict[str, Any]] = []
        current_weight = 0.0
        current_volume = 0.0

        for item in sorted_shipments:
            reason = cls.why_not_fit(truck, packed, current_weight, current_volume, item)
            if reason:
                unpacked.append({"item": item, "reason": reason})
                continue
            packed.append(item)
            current_weight += item.weight_kg
            current_volume += cls.item_volume(item)

        return {
            "truck_id": truck.id,
            "total_packed_weight_kg": round(current_weight, 2),
            "total_packed_volume_cbm": round(current_volume, 3),
            **cls._fill(truck, current_weight, current_volume),
            "packed_items": packed,
            "unpacked_items": unpacked,
        }

    @classmethod
    def assign_to_trucks(
        cls,
        trucks: List[TruckSpec],
        shipments: List[ShipmentItem],
    ) -> Dict[str, Any]:
        """
        Spread a pool's shipments over SEVERAL trucks (First-Fit Decreasing bin-packing).

        1. Sort shipments biggest first. "Big" = the larger of its share of truck
           weight and its share of truck volume, so a light but bulky carton
           counts as big too.
        2. Put each shipment in the first truck (in the order given) where it still
           fits by weight, volume, size and compatibility.
        3. Anything that fits no truck is returned as a leftover with the reason.

        A truck is never loaded past its weight or volume limit.
        Put preferred trucks (e.g. cheapest per km) first in `trucks`.
        """
        if not trucks:
            return {
                "trucks": [],
                "leftover_items": [{"item": s, "reason": "No trucks given"} for s in shipments],
                "trucks_used": 0,
            }

        ref_weight = max(t.max_weight_kg for t in trucks)
        ref_volume = max(t.max_volume_cbm for t in trucks)

        def size(s: ShipmentItem) -> float:
            return max(s.weight_kg / ref_weight, cls.item_volume(s) / ref_volume)

        order = sorted(shipments, key=lambda s: (-size(s), s.id))
        loads = [{"truck": t, "items": [], "weight": 0.0, "volume": 0.0} for t in trucks]
        leftover: List[Dict[str, Any]] = []

        for item in order:
            reasons = []
            for load in loads:
                reason = cls.why_not_fit(load["truck"], load["items"], load["weight"], load["volume"], item)
                if reason is None:
                    load["items"].append(item)
                    load["weight"] += item.weight_kg
                    load["volume"] += cls.item_volume(item)
                    break
                reasons.append(f"truck {load['truck'].id}: {reason}")
            else:
                leftover.append({"item": item, "reason": cls._leftover_reason(trucks, item, reasons)})

        trucks_out = []
        for load in loads:
            t = load["truck"]
            trucks_out.append({
                "truck_id": t.id,
                "shipment_ids": [i.id for i in load["items"]],
                "packed_items": load["items"],
                "total_weight_kg": round(load["weight"], 2),
                "total_volume_cbm": round(load["volume"], 3),
                "remaining_weight_kg": round(t.max_weight_kg - load["weight"], 2),
                "remaining_volume_cbm": round(t.max_volume_cbm - load["volume"], 3),
                **cls._fill(t, load["weight"], load["volume"]),
            })
        return {
            "trucks": trucks_out,
            "leftover_items": leftover,
            "trucks_used": sum(1 for t in trucks_out if t["shipment_ids"]),
        }

    @classmethod
    def _leftover_reason(cls, trucks: List[TruckSpec], item: ShipmentItem, reasons: List[str]) -> str:
        """Explain why a shipment went in no truck, in plain words."""
        if all(cls.why_not_fit(t, [], 0.0, 0.0, item) for t in trucks):
            return "Too big for every truck even when empty (" + "; ".join(reasons) + ")"
        return "No truck has room left for it (" + "; ".join(reasons) + ")"
