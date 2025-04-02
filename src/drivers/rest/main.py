from fastapi import FastAPI

from src.config.logger import setup_app_logger
from src.drivers.rest.exception_handlers import register_exception_handlers
from src.drivers.rest.routers import calibration_router, tag_router

# Call the logger setup function right at the start
setup_app_logger()

app = FastAPI(
    title="Calibration Service",
    description="API for managing calibrations and tags",
    version="0.1.0",
)

register_exception_handlers(app)
app.include_router(calibration_router.router)
app.include_router(tag_router.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}
