from fastapi import FastAPI
from loguru import logger

# Import Routers
from src.drivers.rest.routers import calibration_router, health_router, tag_router

# Configure logger
logger.add("logs/app.log", rotation="500 MB", level="INFO")

app = FastAPI(
    title="Calibration Service",
    description="Manages device calibrations and associated tags.",
    version="0.1.0",
)

# Include routers
app.include_router(health_router.router)
app.include_router(tag_router.router)
app.include_router(calibration_router.router)

logger.info("FastAPI application startup complete.")
