from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "PoolShip API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "poolship_super_secret_jwt_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    DATABASE_URL: str = "postgresql+asyncpg://poolship:poolship_secret@localhost:5432/poolship_db"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    
    # Baseline emission factor in kg CO2 per ton-km for medium-duty trucks
    CO2_EMISSION_FACTOR_KG_PER_TON_KM: float = 0.15
    AVERAGE_DIESEL_CONSUMPTION_L_PER_KM: float = 0.28  # ~3.5 km/L for trucks

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
