"""E11: config validation (stages/stage_0.md R4; stage_4.md Mission M1)."""

import copy
from pathlib import Path

import pytest
import yaml

from src.common.config import (ConfigError, class_names, load_config,
                               validate_pipeline, validate_taxonomy)

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "configs" / "pipeline.yaml"
TAXONOMY = ROOT / "configs" / "taxonomy.yaml"


@pytest.fixture()
def cfg():
    return yaml.safe_load(PIPELINE.read_text(encoding="utf-8"))


@pytest.fixture()
def tax():
    return yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))


def test_committed_configs_validate():
    merged = load_config(PIPELINE)
    assert merged["taxonomy"]["classes"][0] == "circle"
    assert class_names(merged)[9] == "diamond"


def test_missing_key_named_in_error(cfg):
    del cfg["augment"]["shear_deg"]
    with pytest.raises(ConfigError, match="augment.shear_deg"):
        validate_pipeline(cfg)


def test_loso_name_collision_rejected(cfg):
    seed0 = cfg["seed_set"][0]
    cfg["runs"] = [{"arm": "A1", "seed": seed0, "holdout_source": "github_handdrawn"}]
    with pytest.raises(ConfigError, match="collides"):
        validate_pipeline(cfg)


def test_holdout_run_with_a_free_name_allowed(cfg):
    seed0, seed1 = cfg["seed_set"][:2]
    cfg["runs"] = [{"arm": "A1", "seed": seed1, "holdout_source": "github_handdrawn"},
                   {"arm": "A0", "seed": seed0, "holdout_source": "github_handdrawn"},
                   {"arm": "A1", "seed": seed0, "name": "A1_other",
                    "holdout_source": "github_handdrawn"}]
    validate_pipeline(cfg)


def test_ratios_must_sum_to_one(cfg):
    cfg["split"]["ratios"] = [0.7, 0.2, 0.2]
    with pytest.raises(ConfigError, match="sum to 1"):
        validate_pipeline(cfg)


def test_runs_reference_known_arms_and_seed_set(cfg):
    bad = copy.deepcopy(cfg)
    bad["runs"].append({"arm": "C", "seed": 0})
    with pytest.raises(ConfigError, match="not in arms"):
        validate_pipeline(bad)
    bad = copy.deepcopy(cfg)
    bad["runs"].append({"arm": "B", "seed": 7})
    with pytest.raises(ConfigError, match="seed_set"):
        validate_pipeline(bad)


def test_unfair_runs_rejected(cfg):
    """Stage 4 Mission M1: B with its own seed, epochs and steps is unfair."""
    cfg["runs"] = [
        {"arm": "A0", "seed": 1},
        {"arm": "A1", "seed": 1},
        {"arm": "B", "seed": 1, "epochs": 40, "steps": 72},
    ]
    with pytest.raises(ConfigError, match="only arm and seed may vary"):
        validate_pipeline(cfg)


def test_duplicate_run_rejected(cfg):
    cfg["runs"].append({"arm": "A0", "seed": 0})
    with pytest.raises(ConfigError, match="duplicate run"):
        validate_pipeline(cfg)


def test_steps_per_epoch_null_or_positive_int(cfg):
    cfg["train"]["steps_per_epoch"] = 0
    with pytest.raises(ConfigError, match="steps_per_epoch"):
        validate_pipeline(cfg)
    cfg["train"]["steps_per_epoch"] = 50
    validate_pipeline(cfg)


def test_taxonomy_disable_list_names_known_classes(tax):
    validate_taxonomy(tax)
    tax["no_shear_no_nonuniform_scale"].append("trapezoid")
    with pytest.raises(ConfigError, match="trapezoid"):
        validate_taxonomy(tax)


def test_taxonomy_indices_contiguous(tax):
    tax["classes"][11] = "kite"
    with pytest.raises(ConfigError, match="indices"):
        validate_taxonomy(tax)


def test_split_seed_must_be_int(cfg):
    cfg["split"]["seed"] = 42.5
    with pytest.raises(ConfigError, match="split.seed"):
        validate_pipeline(cfg)


def test_confusion_pairs_checked_against_taxonomy(cfg, tax):
    cfg["evaluation"]["confusion_pairs"] = [["square", "dimond"]]
    cfg["taxonomy"] = tax
    with pytest.raises(ConfigError, match="dimond"):
        validate_pipeline(cfg)


def test_tuning_grid_must_be_numeric_lists(cfg):
    cfg["train"]["tuning"]["lr"] = "0.001"
    with pytest.raises(ConfigError, match="train.tuning.lr"):
        validate_pipeline(cfg)


def test_taxonomy_path_resolved_from_repo_root(tmp_path):
    other = tmp_path / "exp" / "pipeline.yaml"
    other.parent.mkdir()
    other.write_text(PIPELINE.read_text(encoding="utf-8"), encoding="utf-8")
    assert load_config(other)["taxonomy"]["classes"][0] == "circle"
