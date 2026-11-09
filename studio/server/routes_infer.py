"""Score a drawing with the exported ONNX models."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from studio.inference.decode import BadDrawing, decode_png
from studio.inference.predict import infer
from studio.server.schemas import InferRequest
from studio.settings import ARMS

router = APIRouter()


@router.post("/api/infer")
def infer_drawing(req: InferRequest) -> dict:
    unknown = [arm for arm in req.arms if arm not in ARMS]
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown arms: {unknown}")
    try:
        image = decode_png(req.image)
    except BadDrawing as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return infer(image, req.arms)
