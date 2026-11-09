"""Local-only request rules: same-origin POST, JSON only, bounded body size."""

from __future__ import annotations

from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from studio.settings import ALLOWED_HOSTS, MAX_BODY_BYTES


def _reject(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)


class PostGuard(BaseHTTPMiddleware):
    """Applied to POST only; a GET cannot change or compute anything sensitive."""

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin and urlsplit(origin).hostname not in ALLOWED_HOSTS:
                return _reject(403, "foreign origin")
            if not request.headers.get("content-type", "").startswith("application/json"):
                return _reject(415, "JSON only")
            length = request.headers.get("content-length")
            if length is None or not length.isdigit():
                return _reject(411, "content length required")
            if int(length) > MAX_BODY_BYTES:
                return _reject(413, "body too large")
        return await call_next(request)
