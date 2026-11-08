"""E12: frozen hand-off signatures (stages/stage_0.md R6)."""

import inspect

import numpy as np

from src.common import interfaces


def test_transform_protocol_takes_rng():
    params = list(inspect.signature(interfaces.TransformFn.__call__).parameters)
    assert params == ["self", "img", "label", "rng"]

    def ok(img, label, rng):
        return img

    assert isinstance(ok, interfaces.TransformFn)


def test_generator_protocol_is_generate():
    assert not hasattr(interfaces.GeneratorFn, "sample")
    params = list(inspect.signature(interfaces.GeneratorFn.__call__).parameters)
    assert params == ["self", "label", "rng"]

    def gen(label, rng):
        return np.full((64, 64), 255, np.uint8)

    assert isinstance(gen, interfaces.GeneratorFn)


def test_model_handle_exposes_probabilities():
    assert hasattr(interfaces.ModelHandle, "predict_proba")
