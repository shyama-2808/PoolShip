from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


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
        Enforce business & safety compatibility rules:
        - Perishables cannot be mixed with hazardous chemicals.
        - Fragile items require careful load balancing.
        """
        has_hazardous = any(item.is_hazardous for item in existing_items)
        has_perishable = any(item.is_perishable for item in existing_items)

        if candidate.is_hazardous and has_perishable:
            return False, "Hazardous materials cannot be pooled with perishable goods"
        
        if candidate.is_perishable and has_hazardous:
            return False, "Perishable goods cannot be pooled with hazardous chemicals"

        return True, "Compatible"

    @classmethod
    def optimize_load(
        cls,
        truck: TruckSpec,
        candidate_shipments: List[ShipmentItem]
    ) -> Dict[str, Any]:
        """
        Greedy multi-constraint consolidation algorithm (Weight + Volume + 3D bounds + Compatibility).
        Sorts shipments by density / value, packs into truck until constraints are reached.
        """
        # Sort items: prioritize denser/larger items first (Best Fit Decreasing heuristic)
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
            # 1. Compatibility check
            is_compat, reason = cls.check_compatibility(packed, item)
            if not is_compat:
                unpacked.append({"item": item, "reason": reason})
                continue

            # 2. Weight constraint
            if current_weight + item.weight_kg > truck.max_weight_kg:
                unpacked.append({"item": item, "reason": "Exceeds truck weight capacity"})
                continue

            # 3. Volume constraint
            computed_vol = item.volume_cbm if item.volume_cbm and item.volume_cbm > 0 else (
                (item.length_cm * item.width_cm * item.height_cm) / 1_000_000.0
            )
            if current_volume + computed_vol > truck.max_volume_cbm:
                unpacked.append({"item": item, "reason": "Exceeds truck volume capacity"})
                continue

            # 4. Dimensional physical limit check
            if (item.length_cm > truck.length_cm or 
                item.width_cm > truck.width_cm or 
                item.height_cm > truck.height_cm):
                unpacked.append({"item": item, "reason": "Item dimensions exceed truck cargo hold dimensions"})
                continue

            # Pack item
            packed.append(item)
            current_weight += item.weight_kg
            current_volume += computed_vol

        weight_utilization = (current_weight / truck.max_weight_kg) * 100.0 if truck.max_weight_kg > 0 else 0
        volume_utilization = (current_volume / truck.max_volume_cbm) * 100.0 if truck.max_volume_cbm > 0 else 0
        overall_utilization = max(weight_utilization, volume_utilization)

        return {
            "truck_id": truck.id,
            "total_packed_weight_kg": round(current_weight, 2),
            "total_packed_volume_cbm": round(current_volume, 3),
            "weight_utilization_pct": round(weight_utilization, 1),
            "volume_utilization_pct": round(volume_utilization, 1),
            "overall_utilization_pct": round(overall_utilization, 1),
            "packed_items": packed,
            "unpacked_items": unpacked,
        }

