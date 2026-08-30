from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.version import APP_VERSION

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.globals["app_version"] = APP_VERSION
