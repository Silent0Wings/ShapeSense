"""The per-model config files stay in step with the pipeline config."""

import pytest
import yaml

from scripts.export_model_configs import OUT_DIR, model_config
from src.common.config import load_config

CONFIG = load_config()
ARMS = list(CONFIG["arms"])


def _saved(arm):
    return yaml.safe_load((OUT_DIR / f"{arm}.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("arm", ARMS)
def test_each_saved_file_matches_the_pipeline_config(arm):
    assert _saved(arm) == model_config(CONFIG, arm)


@pytest.mark.parametrize("arm", ARMS)
def test_each_batch_adds_up_to_the_batch_size(arm):
    saved = _saved(arm)
    assert sum(saved["batch_mix"]["images_per_batch"].values()) == saved["training"]["batch_size"]


def test_a_model_without_augmentation_or_synthetic_data_lists_none():
    saved = _saved("A0")
    assert saved["augmentation"] is None and saved["generator"] is None


def test_only_the_pretraining_model_has_a_pretraining_phase():
    assert _saved("P")["batch_mix"]["pretraining"]["epochs"] > 0
    assert all(_saved(arm)["batch_mix"]["pretraining"] is None for arm in ARMS if arm != "P")
