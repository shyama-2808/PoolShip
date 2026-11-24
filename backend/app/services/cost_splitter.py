from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

SPLIT_METHODS = ("ton_km", "weight", "volume", "distance")


def to_paise(rupees: float) -> int:
    """₹ to whole paise, rounding half up (₹10.005 -> 1001 paise)."""
    return int((Decimal(str(rupees)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class CostSplitter:
    """
    Transparent cost-splitting engine for PoolShip.

    1. trip_cost(): the truck's price for the trip = distance × rate per km.
    2. calculate_split(): shares that price between the shippers in the pool,
       by weight, volume, distance or ton-km (weight × distance).

    Money is worked out in whole paise, so the shares always add up to the
    trip cost exactly (no ₹0.01 lost or gained to rounding).
    """

    @staticmethod
    def trip_cost(distance_km: float, rate_per_km: float) -> float:
        """Total ₹ for the truck trip, rounded to the paisa."""
        return to_paise(distance_km * rate_per_km) / 100

    @staticmethod
    def _measure(s: Dict[str, Any], method: str) -> float:
        """How much of the truck this shipment 'uses' under the chosen method."""
        weight = s.get("weight_kg") or 0.0
        distance = s.get("distance_km")
        distance = 1.0 if distance is None else distance
        if method == "ton_km":
            return (weight / 1000.0) * distance
        if method == "weight":
            return weight
        if method == "volume":
            return s.get("volume_cbm") or 0.0
        return distance  # "distance"

    @staticmethod
    def _split_paise(total_paise: int, weights: List[float]) -> List[int]:
        """
        Share total_paise in proportion to weights, in whole paise, summing exactly.
        Everyone gets the rounded-down amount, then the few paise left over go one
        each to the shares that were rounded down the most (largest remainder).
        """
        n = len(weights)
        total_w = sum(weights)
        if total_w <= 0:
            weights, total_w = [1.0] * n, float(n)  # nothing to go on: split equally
        exact = [Decimal(total_paise) * Decimal(repr(w)) / Decimal(repr(total_w)) for w in weights]
        paise = [int(e) for e in exact]  # floor (all values are >= 0)
        left = total_paise - sum(paise)
        by_remainder = sorted(range(n), key=lambda i: (-(exact[i] - paise[i]), i))
        for i in by_remainder[:left]:
            paise[i] += 1
        return paise

    @classmethod
    def calculate_split(
        cls,
        total_trip_cost: float,
        shipments: List[Dict[str, Any]],
        split_method: str = "ton_km",
    ) -> List[Dict[str, Any]]:
        """
        Each shipper's share of the truck trip cost.

        Args:
            total_trip_cost: Total ₹ for the truck trip (e.g. ₹12,000).
            shipments: dicts with 'id', 'weight_kg', and where needed 'volume_cbm', 'distance_km'.
            split_method:
                'weight'   - in proportion to kg
                'volume'   - in proportion to m³
                'distance' - in proportion to how far each shipment travels
                'ton_km'   - in proportion to tonnes × km (standard freight)
        If nobody has any of the chosen measure (e.g. all volumes 0), the cost is split equally.
        """
        if split_method not in SPLIT_METHODS:
            raise ValueError(
                f"Unknown split_method '{split_method}'. Use one of: {', '.join(SPLIT_METHODS)}."
            )
        if not shipments:
            return []

        total_paise = to_paise(total_trip_cost)
        measures = [cls._measure(s, split_method) for s in shipments]
        paise = cls._split_paise(total_paise, measures)
        total_measure = sum(measures)

        results = []
        for s, m, p in zip(shipments, measures, paise):
            ratio = m / total_measure if total_measure > 0 else 1.0 / len(shipments)
            savings_paise = total_paise - p  # vs hiring the whole truck alone
            row = {
                "shipment_id": s["id"],
                "share_ratio": round(ratio, 4),
                "allocated_cost": p / 100,
                "allocated_paise": p,
                "savings_vs_dedicated_trip": savings_paise / 100,
                "savings_percentage": round(savings_paise * 100 / total_paise, 1) if total_paise else 0.0,
            }
            if split_method == "ton_km":
                row["ton_km"] = round(m, 2)
            results.append(row)
        return results
