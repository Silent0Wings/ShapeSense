"""The dashboard's training recipes match the code that builds the batches."""

import torch

from src.common.config import load_config
from src.stage4_train.model import build_model, count_params
from src.stage4_train.sampling import batch_composition, clean_count
from studio.data import architecture


def test_recipes_match_the_real_batch_composition():
    config = load_config()
    batch = int(config["train"]["batch_size"])
    recipes = {r["arm"]: r for r in architecture.recipes()}
    assert set(recipes) == set(config["arms"])
    for arm, arm_cfg in config["arms"].items():
        real, synthetic = batch_composition(arm_cfg, batch, float(config["synthetic_fraction"]))
        recipe = recipes[arm]
        assert recipe["synthetic"] == synthetic and recipe["clean"] + recipe["augmented"] == real
        if arm_cfg["augment"]:
            assert recipe["clean"] == clean_count(arm_cfg, batch)
        else:
            assert recipe["augmented"] == 0


def test_only_the_pretraining_arm_has_a_pretraining_phase():
    recipes = {r["arm"]: r for r in architecture.recipes()}
    assert recipes["P"]["pretrain_epochs"] > 0 and recipes["P"]["pretrain_synthetic"] == recipes["P"]["clean"] + recipes["P"]["augmented"]
    assert all(r["pretrain_epochs"] == 0 for arm, r in recipes.items() if arm != "P")


def test_the_diagram_matches_the_real_model():
    config = load_config()
    ops = architecture.network()
    model = build_model(config, n_classes=10, dropout=0.2)
    assert sum(op["params"] for op in ops) == count_params(model)
    x = torch.zeros(2, int(config["image_channels"]), int(config["image_size"]), int(config["image_size"]))
    drawn = [op for op in ops if op["group"].startswith("Block")]
    assert len(drawn) == len(model.features)
    model.eval()
    with torch.no_grad():
        for op, layer in zip(drawn, model.features):
            x = layer(x)
            assert list(x.shape[1:]) == op["output"], op["id"]
    assert ops[-1]["output"] == [10]


def test_the_last_convolution_block_sees_the_documented_area():
    pools = [op for op in architecture.network() if op["kind"] == "maxpool"]
    assert pools[-1]["sees"] == 46
