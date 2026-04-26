from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from server.routes import config_routes, file_routes, run_routes

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
    cache_size=0,
)


def render_template(name: str, **kwargs) -> HTMLResponse:
    template = _jinja_env.get_template(name)
    return HTMLResponse(template.render(**kwargs))


def create_app() -> FastAPI:
    app = FastAPI(title="SRT-SUMMARIZER", version="2.0.0")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def index(request: Request):
        return render_template("index.html", request=request)

    app.include_router(config_routes.router)
    app.include_router(file_routes.router)
    app.include_router(run_routes.router)

    return app
