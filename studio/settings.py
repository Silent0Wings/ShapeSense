"""Every fixed number and location of the studio, in one place."""

from __future__ import annotations

from pathlib import Path

HOST = "127.0.0.1"             # local only; there is deliberately no option to change it
PORT = 8765
ALLOWED_HOSTS = ("127.0.0.1", "localhost")

PACKAGE_DIR = Path(__file__).resolve().parent
WEB_DIR = PACKAGE_DIR / "web"
ARMS_DIR = PACKAGE_DIR / "out" / "arms"
ARMS_MANIFEST = ARMS_DIR / "manifest.json"

ARMS = ("A0", "A1", "B")
POOL_SPLITS = ("train", "val")     # the only splits a browsing page may ask for
AUGMENT_SPLIT = "train"            # Stage 2 runs on the training side only

NOT_SURE_BELOW = 0.5               # same threshold as demo/logic.py
TOP_K = 3
MAX_SAMPLES = 24
MAX_VARIANTS = 64
MAX_GROUP_IMAGES = 12
MAX_ERRORS_PAGE = 24
MAX_BODY_BYTES = 3 * 1024 * 1024
MAX_PNG_BYTES = 2 * 1024 * 1024
MAX_PNG_SIDE = 2048
