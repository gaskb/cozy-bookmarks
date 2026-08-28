from fastapi import FastAPI

from app.api.health import router as health_router
from app.logging_config import configure_logging

configure_logging()

app = FastAPI(title="cozy-bookmarks")
app.include_router(health_router)
