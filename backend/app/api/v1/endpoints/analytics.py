from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.pool import Pool
from app.models.shipment import Shipment
from app.models.truck import Truck
from app.services.carbon_calculator import CarbonCalculator

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Summary metrics for the Admin and Carbon Savings dashboards."""
    total_pools = await db.scalar(select(func.count(Pool.id))) or 0
    total_shipments = await db.scalar(select(func.count(Shipment.id)).where(Shipment.pool_id.is_not(None))) or 0
    total_trucks = await db.scalar(select(func.count(Truck.id))) or 0

    co2_saved = await db.scalar(select(func.sum(Pool.co2_saved_kg))) or 0.0
    diesel_saved = await db.scalar(select(func.sum(Pool.diesel_saved_litres))) or 0.0
    avg_utilization = await db.scalar(select(func.avg(Pool.utilization_percentage))) or 0.0

    return {
        "platform_metrics": {
            "total_pools": total_pools,
            "total_shipments_pooled": total_shipments,
            "active_trucks": total_trucks,
            "average_truck_utilization_pct": round(avg_utilization, 1),
        },
        "environmental_impact": {
            "total_co2_saved_kg": round(co2_saved, 2),
            "total_diesel_saved_litres": round(diesel_saved, 2),
            "equivalent_trees_planted": round(co2_saved / 21.77, 1),  # ~21.77 kg CO2 absorbed per tree/year
            "emission_factors": CarbonCalculator.emission_factors(),
        }
    }
