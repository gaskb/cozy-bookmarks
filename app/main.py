from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.bookmarks import router as bookmarks_router
from app.api.health import router as health_router
from app.api.quick_save import router as quick_save_router
from app.logging_config import configure_logging
from app.web.auth import router as web_auth_router
from app.web.bookmarks import router as web_bookmarks_router
from app.web.deps import NotAuthenticatedRedirect

configure_logging()

app = FastAPI(title="cozy-bookmarks")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(bookmarks_router)
app.include_router(quick_save_router)
app.include_router(web_auth_router)
app.include_router(web_bookmarks_router)

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "web" / "static")),
    name="static",
)


@app.exception_handler(NotAuthenticatedRedirect)
def redirect_to_login(request, exc: NotAuthenticatedRedirect) -> RedirectResponse:
    return RedirectResponse("/login", status_code=303)
