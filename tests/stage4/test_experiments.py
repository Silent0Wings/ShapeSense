"""Iteration 3 experiment designs match the pre-registration."""

from src.common.config import load_config
from src.stage4_train import experiments as ex


def _cfg():
    return load_config()


def test_run_counts_match_the_preregistration():
    cfg = _cfg()
    assert len(ex.scarcity_specs(cfg, "c")) == 60
    assert len(ex.equal_real_specs(cfg, "c")) == 6
    assert len(ex.budget_specs(cfg, "c")) == 27
    assert len(ex.one_on_specs(cfg, "c")) == 15


def test_trial_names_are_unique():
    names = [s["run_name"] for s in ex.all_specs(_cfg(), "c")]
    assert len(names) == len(set(names))


def test_equal_real_is_switched_on_only_for_its_arm():
    for spec in ex.equal_real_specs(_cfg(), "c"):
        assert spec["overrides"][f"arms.{spec['arm']}.equal_real"] is True


def test_one_transform_on_leaves_the_others_off():
    specs = {s["run_name"].rsplit("_s", 1)[0]: s for s in ex.one_on_specs(_cfg(), "c")}
    rotation = specs["exp_one_on_rotation"]["overrides"]
    assert rotation["augment.rotate_deg"] > 0 and rotation["augment.noise_p"] == 0.0
    only = specs["exp_one_on_reframe_only"]["overrides"]
    assert only["augment.rotate_deg"] == 0 and only["augment.blur_p"] == 0.0 and only["augment.scale"] == [1.0, 1.0]


def test_measuring_a_shape_reports_its_proportions():
    import numpy as np

    image = np.full((64, 64), 255, dtype=np.uint8)
    image[20:44, 10:54] = 0
    image[23:41, 13:51] = 255
    aspect, stroke = ex._measure(image)
    assert 1.7 < aspect < 2.0 and 2.0 < stroke < 8.0
