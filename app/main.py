from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.bookmarks import router as bookmarks_router
from app.api.health import router as health_router
from app.api.quick_save import router as quick_save_router
from app.logging_config import configure_logging

configure_logging()

app = FastAPI(title="cozy-bookmarks")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(bookmarks_router)
app.include_router(quick_save_router)
