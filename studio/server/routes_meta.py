"""Page bundles and allow-listed files."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from src.common.config import REPO_ROOT

from studio import allowlist
from studio.data import pages

router = APIRouter()


def _missing(detail: str = "not found") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


@router.get("/api/meta")
def meta() -> dict:
    return pages.meta()


@router.get("/api/page/{name}")
def page(name: str) -> dict:
    bundle = pages.build(name)
    if bundle is None:
        raise _missing()
    return bundle


@router.get("/img/{key}")
def image(key: str) -> FileResponse:
    if key not in allowlist.IMAGES:
        raise _missing()
    path = allowlist.image_path(key)
    if not path.is_file():
        raise _missing("this stage has not produced that image yet")
    return FileResponse(path, media_type="image/png")


@router.get("/file/{key}")
def file(key: str) -> FileResponse:
    if key not in allowlist.FILES:
        raise _missing()
    relative, media_type = allowlist.FILES[key]
    path = REPO_ROOT / relative
    if not path.is_file():
        raise _missing("this file has not been built yet")
    return FileResponse(path, media_type=media_type)
