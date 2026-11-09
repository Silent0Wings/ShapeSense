"""Requests outside the allowed ranges are refused before any work happens."""

import base64
import io

import pytest
from PIL import Image
from starlette.testclient import TestClient

from studio import allowlist
from studio.data import samples
from studio.ops.overrides import default_augment_values
from studio.server.app import create_app
from studio.settings import MAX_BODY_BYTES, MAX_PNG_SIDE


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(), base_url="http://127.0.0.1:8765")


def _augment(values=None, **kw):
    return {"label": 0, "index": 0, "seed": 0, "n": 1, "values": values or default_augment_values(), **kw}


def test_test_split_refused_before_any_file_read(client, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the catalog was reached")
    monkeypatch.setattr(samples, "load_split_rows", boom)
    monkeypatch.setattr(samples, "image_paths", boom)
    assert client.get("/api/samples?label=0&split=test").status_code == 403
    assert client.get("/api/class-stats?label=0&split=test").status_code == 403
    assert client.get("/api/group?group=x&split=test").status_code == 403


def test_pool_refuses_other_splits_directly():
    with pytest.raises(samples.SplitNotAllowed):
        samples._pool("test")


@pytest.mark.parametrize("field,value", [("rotate_deg", 999), ("noise_p", -0.1), ("scale_lo", 2.0)])
def test_out_of_range_sliders_rejected(client, field, value):
    values = {**default_augment_values(), field: value}
    assert client.post("/api/augment", json=_augment(values)).status_code == 422


def test_unknown_fields_and_huge_counts_rejected(client):
    assert client.post("/api/augment", json=_augment(extra=1)).status_code == 422
    assert client.post("/api/augment", json=_augment(n=10_000)).status_code == 422


@pytest.mark.parametrize("key", ["secret", "..%2F..%2Fconfigs%2Fsplits%2Ftest.csv", "test.csv"])
def test_unknown_image_and_file_keys_are_404(client, key):
    assert client.get(f"/img/{key}").status_code == 404
    assert client.get(f"/file/{key}").status_code == 404


def test_static_mount_cannot_escape_web_folder(client):
    for url in ("/..%2F..%2Fconfigs%2Fsplits%2Ftest.csv", "/../../configs/splits/test.csv"):
        response = client.get(url)
        assert response.status_code == 404 or b"image_id" not in response.content


def test_allowlist_has_no_test_derived_source_paths():
    every = list(allowlist.DOCS.values()) + list(allowlist.IMAGES.values())
    assert not [p for p in every if "splits" in p or p.startswith("data_set") or "rebuild" in p]


def test_foreign_host_and_origin_rejected():
    app = create_app()
    assert TestClient(app, base_url="http://evil.example").get("/api/meta").status_code == 400
    local = TestClient(app, base_url="http://127.0.0.1:8765")
    response = local.post("/api/whatif", json={"min_gain": 1, "max_class_drop": 2, "require_ci": True},
                          headers={"Origin": "http://evil.example"})
    assert response.status_code == 403


def test_post_must_be_json_and_bounded(client):
    assert client.post("/api/whatif", content="x", headers={"Content-Type": "text/plain"}).status_code == 415
    huge = "x" * (MAX_BODY_BYTES + 1)
    assert client.post("/api/whatif", content=huge, headers={"Content-Type": "application/json"}).status_code == 413


def _png(side):
    buf = io.BytesIO()
    Image.new("RGB", (side, side), "white").save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def test_non_png_and_oversized_drawings_rejected(client):
    assert client.post("/api/infer", json={"image": "data:text/plain;base64,AA==", "arms": []}).status_code == 422
    assert client.post("/api/infer", json={"image": _png(MAX_PNG_SIDE + 1), "arms": []}).status_code == 422
    assert client.post("/api/infer", json={"image": _png(64), "arms": ["C9"]}).status_code == 422
