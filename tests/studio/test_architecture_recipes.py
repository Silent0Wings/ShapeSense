"""The dashboard's training recipes match the code that builds the batches."""

from src.common.config import load_config
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
