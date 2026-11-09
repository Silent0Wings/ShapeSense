"""Stage 4 run records, Stage 5 confusion counts, stored errors, the what-if rule."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from studio.data import confusion, errors, runs, whatif
from studio.server.schemas import WhatIfRequest
from studio.settings import ARMS

router = APIRouter()


@router.get("/api/stage4/run/{run}")
def run_record(run: str) -> dict:
    record = runs.record(run)
    if record is None:
        raise HTTPException(status_code=404, detail="unknown run")
    return record


@router.get("/api/stage5/confusion/{arm}")
def confusion_counts(arm: str) -> dict:
    if arm not in ARMS:
        raise HTTPException(status_code=404, detail="unknown arm")
    matrix = confusion.counts(arm)
    if matrix is None:
        raise HTTPException(status_code=404, detail="Stage 5 has not run")
    return {"arm": arm, "matrix": matrix}


@router.get("/api/stage5/errors")
def stored_errors(true: int = Query(ge=0, le=9), pred: int = Query(ge=0, le=9),
                  offset: int = Query(default=0, ge=0)) -> dict:
    if (true, pred) not in errors.allowed_cells():
        return {"total": 0, "offset": 0, "images": [], "available": False}
    result = errors.page(true, pred, offset)
    if result is None:
        raise HTTPException(status_code=404, detail="Stage 5 has not run")
    return {**result, "available": True}


@router.post("/api/whatif")
def what_if(req: WhatIfRequest) -> dict:
    result = whatif.evaluate(req.min_gain, req.max_class_drop, req.require_ci)
    if result is None:
        raise HTTPException(status_code=404, detail="Stage 5 has not run")
    return result
