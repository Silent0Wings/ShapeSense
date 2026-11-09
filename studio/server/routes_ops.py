"""Live examples: browse train/val images, run the real augmentation and generator."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from studio.data import samples
from studio.imaging import to_b64_png
from studio.ops import augment as augment_ops
from studio.ops import synth as synth_ops
from studio.server.schemas import AugmentRequest, SynthRequest
from studio.settings import AUGMENT_SPLIT, MAX_GROUP_IMAGES, MAX_SAMPLES, POOL_SPLITS

router = APIRouter()


def _allow(split: str) -> None:
    """Runs before any file is opened: only train and val may be browsed."""
    if split not in POOL_SPLITS:
        raise HTTPException(status_code=403, detail="only the train and val splits can be browsed")


@router.get("/api/samples")
def browse(label: int = Query(ge=0, le=9), split: str = "train",
           n: int = Query(default=12, ge=1, le=MAX_SAMPLES), seed: int = Query(default=0, ge=0)) -> dict:
    _allow(split)
    images, rows = samples.pick(split, label, n, seed)
    return {"items": [{"image": to_b64_png(im), "source": r["source_id"]}
                      for im, r in zip(images, rows)]}


@router.get("/api/class-stats")
def class_stats(label: int = Query(ge=0, le=9), split: str = "train",
                seed: int = Query(default=0, ge=0)) -> dict:
    _allow(split)
    stats = samples.class_stats(split, label, 200, seed)
    if stats is None:
        raise HTTPException(status_code=404, detail="no images for this class")
    return {"mean": to_b64_png(stats["mean"]), "spread": to_b64_png(stats["std"]), "n": stats["n"]}


@router.get("/api/group")
def group(group: str = Query(max_length=64), split: str = "train") -> dict:
    _allow(split)
    images = samples.group_images(split, group, MAX_GROUP_IMAGES)
    return {"images": [to_b64_png(im) for im in images]}


@router.post("/api/augment")
def augment(req: AugmentRequest) -> dict:
    found = samples.nth(AUGMENT_SPLIT, req.label, req.index)
    if found is None:
        raise HTTPException(status_code=404, detail="no images for this class")
    image, row = found
    return {"source": row["source_id"],
            **augment_ops.preview(image, req.label, req.values.model_dump(), req.seed, req.n, req.uncapped)}


@router.post("/api/synth")
def synth(req: SynthRequest) -> dict:
    try:
        return {"items": synth_ops.preview(req.label, req.values.model_dump(), req.seed, req.n)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
