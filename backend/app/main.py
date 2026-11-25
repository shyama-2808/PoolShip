from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401  (registers all tables on Base.metadata)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create any missing tables on startup (there are no migrations yet).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all doesn't add new columns to tables that already exist
        if conn.dialect.name == "postgresql":
            await conn.execute(text("ALTER TABLE pools ADD COLUMN IF NOT EXISTS split_method VARCHAR"))
            await conn.execute(text(
                "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS temperature_class VARCHAR DEFAULT 'ambient'"
            ))
            await conn.execute(text(
                "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS recurring_id INTEGER REFERENCES recurring_shipments(id)"
            ))
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Peer-to-peer freight pooling platform API for small businesses and transporters.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }

