"""Request bodies. Every field has hard bounds; unknown fields are rejected."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from studio.settings import ARMS, MAX_BODY_BYTES, MAX_VARIANTS


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AugmentValues(_Strict):
    rotate_deg: float = Field(ge=0, le=180)
    scale_lo: float = Field(ge=0.5, le=1.5)
    scale_hi: float = Field(ge=0.5, le=1.5)
    nonuniform_scale: float = Field(ge=0, le=1)
    shear_deg: float = Field(ge=0, le=45)
    translate_px: float = Field(ge=0, le=16)
    noise_p: float = Field(ge=0, le=1)
    blur_p: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _ordered(self):
        if self.scale_lo > self.scale_hi:
            raise ValueError("scale_lo must not exceed scale_hi")
        return self


class AugmentRequest(_Strict):
    label: int = Field(ge=0, le=9)
    index: int = Field(ge=0, le=1_000_000)
    seed: int = Field(ge=0, le=2**31)
    n: int = Field(ge=1, le=MAX_VARIANTS)
    values: AugmentValues


class SynthValues(_Strict):
    radius_lo: float = Field(ge=8, le=30)
    radius_hi: float = Field(ge=8, le=30)
    center_jitter_px: float = Field(ge=0, le=12)
    vertex_jitter_px: float = Field(ge=0, le=4)
    ellipse_max_axis_ratio: float = Field(ge=1.25, le=4)
    rectangle_max_side_ratio: float = Field(ge=1.25, le=4)
    diamond_lo: float = Field(ge=20, le=80)
    diamond_hi: float = Field(ge=20, le=80)
    star_lo: float = Field(ge=0.2, le=0.6)
    star_hi: float = Field(ge=0.2, le=0.6)

    @model_validator(mode="after")
    def _ordered(self):
        for lo, hi in ((self.radius_lo, self.radius_hi), (self.diamond_lo, self.diamond_hi),
                       (self.star_lo, self.star_hi)):
            if lo > hi:
                raise ValueError("a range minimum must not exceed its maximum")
        return self


class SynthRequest(_Strict):
    label: int = Field(ge=0, le=9)
    seed: int = Field(ge=0, le=2**31)
    n: int = Field(ge=1, le=MAX_VARIANTS)
    values: SynthValues


class InferRequest(_Strict):
    image: str = Field(max_length=MAX_BODY_BYTES)
    arms: list[str] = Field(max_length=len(ARMS))


class WhatIfRequest(_Strict):
    min_gain: float = Field(ge=-20, le=20)
    max_class_drop: float = Field(ge=0, le=50)
    require_ci: bool
