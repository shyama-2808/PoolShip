from fastapi import APIRouter
from app.api.v1.endpoints import auth, shipments, trucks, pools, tracking, analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(shipments.router, prefix="/shipments", tags=["Shipments"])
api_router.include_router(trucks.router, prefix="/trucks", tags=["Trucks"])
api_router.include_router(pools.router, prefix="/pools", tags=["Pools & Consolidation"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["Live Tracking"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Carbon"])
