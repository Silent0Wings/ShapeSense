"""The local application: API routes first, then the static pages."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from studio.server import routes_eval, routes_infer, routes_meta, routes_ops
from studio.server.security import PostGuard
from studio.settings import ALLOWED_HOSTS, WEB_DIR


def create_app() -> FastAPI:
    app = FastAPI(title="ShapeSense Studio", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(PostGuard)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(ALLOWED_HOSTS))
    for module in (routes_meta, routes_ops, routes_eval, routes_infer):
        app.include_router(module.router)
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
