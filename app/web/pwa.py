from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent / "static"

MANIFEST = {
    "name": "Cozy Bookmarks",
    "short_name": "Cozy Bookmarks",
    "description": "Salva link disorganizzati, organizzali dopo.",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": "#faf7f2",
    "theme_color": "#b5651d",
    "icons": [
        {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {
            "src": "/static/icons/icon-512-maskable.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable",
        },
    ],
    "share_target": {
        "action": "/share-target",
        "method": "POST",
        "enctype": "application/x-www-form-urlencoded",
        "params": {"title": "title", "text": "text", "url": "url"},
    },
}


@router.get("/manifest.json")
def manifest() -> JSONResponse:
    return JSONResponse(MANIFEST, media_type="application/manifest+json")


@router.get("/sw.js")
def service_worker() -> FileResponse:
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")
