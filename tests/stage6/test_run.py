"""Stage 6 runner helpers (audit finding 8): the export smoke test must say
whether the procedurally drawn hexagon was predicted "hexagon", without
failing the stage on a wrong class (a weak model is a result, not a broken
export). No subprocess, no bundle: the verdict function is pure.
"""

from src.stage6_report import run as s6

LABELS = ["circle", "ellipse", "triangle", "square", "rectangle", "pentagon",
          "hexagon", "octagon", "star", "diamond"]


def test_smoke_requires_hexagon_but_does_not_fail_stage():
    assert s6.SMOKE_EXPECTED_CLASS == "hexagon"
    assert s6.SMOKE_SIDES == 6

    right = s6.smoke_verdict(0, "hexagon\n", LABELS)
    assert right == {"predicted": "hexagon", "ok": True, "matches_expected": True}

    # A valid but wrong class: the bundle works (ok) and the mismatch is surfaced.
    wrong = s6.smoke_verdict(0, "some warning line\nsquare\n", LABELS)
    assert wrong["predicted"] == "square"
    assert wrong["ok"] is True
    assert wrong["matches_expected"] is False

    # Not a class name, or a crashed interpreter: the bundle is broken.
    assert s6.smoke_verdict(0, "Traceback ...\n", LABELS)["ok"] is False
    assert s6.smoke_verdict(1, "hexagon\n", LABELS)["ok"] is False
    assert s6.smoke_verdict(1, "hexagon\n", LABELS)["matches_expected"] is False
    empty = s6.smoke_verdict(0, "", LABELS)
    assert empty["predicted"] is None and empty["ok"] is False


def test_smoke_test_reports_missing_bundle(tmp_path):
    config = {"taxonomy": {"classes": dict(enumerate(LABELS))}}
    result = s6.smoke_test(config, tmp_path, tmp_path / "img.png")
    assert result["ok"] is False
    assert result["matches_expected"] is False
    assert set(result["missing_files"]) == set(s6.EXPORT_REQUIRED)
