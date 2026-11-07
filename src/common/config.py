"""Config loading shared by all stages. Configs live in configs/ and are
frozen by Stage 1; changing them after the freeze needs team agreement.
"""

import yaml


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
