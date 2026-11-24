from typing import List, Dict, Any


class CostSplitter:
    """
    Transparent cost-splitting engine for PoolShip.
    Allocates freight expenditure among participating shippers using the standard Ton-Kilometer (TK) model.
    """

    @staticmethod
    def calculate_split(
        total_trip_cost: float,
        shipments: List[Dict[str, Any]],
        split_method: str = "ton_km"
    ) -> List[Dict[str, Any]]:
        """
        Calculates each shipper's fair share of the truck trip cost.
        
        Args:
            total_trip_cost: Total fee agreed for the truck route (e.g. ₹18,000).
            shipments: List of dicts with keys: 'id', 'weight_kg', 'distance_km', optional 'volume_cbm'
            split_method: 'ton_km' (standard freight), 'weight', or 'volume'
        """
        if not shipments:
            return []

        results = []

        if split_method == "ton_km":
            # Weight in Metric Tons * Distance in KM
            ton_kms = []
            for s in shipments:
                tons = s.get("weight_kg", 0.0) / 1000.0
                dist = s.get("distance_km", 1.0)
                ton_kms.append(tons * dist)

            total_ton_km = sum(ton_kms)
            if total_ton_km <= 0:
                # Fallback to equal split if 0 ton-km
                equal_share = round(total_trip_cost / len(shipments), 2)
                for s in shipments:
                    results.append({
                        "shipment_id": s["id"],
                        "share_ratio": round(1.0 / len(shipments), 4),
                        "allocated_cost": equal_share,
                        "savings_vs_dedicated_trip": round(total_trip_cost - equal_share, 2),
                    })
                return results

            for s, tk in zip(shipments, ton_kms):
                ratio = tk / total_ton_km
                share = round(ratio * total_trip_cost, 2)
                # Baseline: what the shipper would have paid if they hired a dedicated truck alone
                dedicated_baseline = total_trip_cost
                savings = round(dedicated_baseline - share, 2)
                savings_pct = round((savings / dedicated_baseline) * 100, 1)

                results.append({
                    "shipment_id": s["id"],
                    "ton_km": round(tk, 2),
                    "share_ratio": round(ratio, 4),
                    "allocated_cost": share,
                    "savings_vs_dedicated_trip": savings,
                    "savings_percentage": savings_pct,
                })

        elif split_method == "weight":
            total_weight = sum(s.get("weight_kg", 0.0) for s in shipments)
            for s in shipments:
                ratio = s.get("weight_kg", 0.0) / total_weight if total_weight > 0 else 1.0 / len(shipments)
                share = round(ratio * total_trip_cost, 2)
                results.append({
                    "shipment_id": s["id"],
                    "share_ratio": round(ratio, 4),
                    "allocated_cost": share,
                    "savings_vs_dedicated_trip": round(total_trip_cost - share, 2),
                })

        return results

