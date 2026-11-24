from typing import List, Dict, Any


class CarbonCalculator:
    """
    Environmental impact & Green logistics engine for PoolShip.
    Compares baseline emissions (each shipper booking a separate truck) against
    the pooled trip emissions to quantify CO2 and diesel reductions.
    """

    # Industry constants for Indian freight (medium-duty diesel trucks):
    DIESEL_LITRES_PER_KM = 0.28          # ~3.57 km/L
    KG_CO2_PER_LITRE_DIESEL = 2.68       # Standard DEFRA / EPA emission factor for diesel
    AVG_CO2_KG_PER_KM = DIESEL_LITRES_PER_KM * KG_CO2_PER_LITRE_DIESEL  # ~0.75 kg CO2/km

    @classmethod
    def calculate_savings(
        cls,
        pooled_route_distance_km: float,
        num_participants: int,
        detour_km: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculates environmental savings.
        
        Args:
            pooled_route_distance_km: Distance driven by the single consolidated truck.
            num_participants: Number of independent shippers sharing this truck.
            detour_km: Extra kilometers incurred due to multiple pick-up/drop-off stops.
        """
        if num_participants <= 1:
            return {
                "baseline_truck_km": round(pooled_route_distance_km, 1),
                "pooled_truck_km": round(pooled_route_distance_km, 1),
                "km_avoided": 0.0,
                "diesel_saved_litres": 0.0,
                "co2_saved_kg": 0.0,
                "co2_reduction_percentage": 0.0,
            }

        # Baseline: Each business would have hired their own truck for their route
        baseline_truck_km = pooled_route_distance_km * num_participants
        actual_pooled_km = pooled_route_distance_km + detour_km

        km_avoided = max(0.0, baseline_truck_km - actual_pooled_km)
        diesel_saved_litres = km_avoided * cls.DIESEL_LITRES_PER_KM
        co2_saved_kg = diesel_saved_litres * cls.KG_CO2_PER_LITRE_DIESEL
        
        baseline_co2 = baseline_truck_km * cls.AVG_CO2_KG_PER_KM
        reduction_pct = (co2_saved_kg / baseline_co2) * 100.0 if baseline_co2 > 0 else 0.0

        return {
            "baseline_truck_km": round(baseline_truck_km, 1),
            "pooled_truck_km": round(actual_pooled_km, 1),
            "km_avoided": round(km_avoided, 1),
            "diesel_saved_litres": round(diesel_saved_litres, 1),
            "co2_saved_kg": round(co2_saved_kg, 1),
            "co2_reduction_percentage": round(reduction_pct, 1),
        }

