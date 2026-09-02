import pytest

from panels.base import DisplayConfig, create_panel


PANEL_CASES = [
    ("progress", "empty", {}, "waiting"),
    ("progress", "missing", {"title": "TEST"}, "waiting"),
    ("progress", "null", {"progress": None}, "waiting"),
    ("progress", "empty_arrays", {"progress": 50, "tags": []}, "ok"),
    ("progress", "invalid_type", {"progress": "not-a-number"}, "error"),
    ("progress", "long_text", {"progress": 50, "title": "X" * 500}, "ok"),
    ("stats", "empty", {}, "waiting"),
    ("stats", "missing", {"title": "TEST"}, "waiting"),
    ("stats", "null", {"primary_value": None}, "waiting"),
    (
        "stats",
        "empty_arrays",
        {"primary_value": "1", "breakdown": []},
        "ok",
    ),
    (
        "stats",
        "invalid_type",
        {"primary_value": "1", "breakdown": "bad"},
        "error",
    ),
    (
        "stats",
        "long_text",
        {"primary_value": "1", "title": "X" * 500},
        "ok",
    ),
    ("flow", "empty", {}, "waiting"),
    ("flow", "missing", {"title": "TEST"}, "waiting"),
    ("flow", "null", {"stages": None}, "error"),
    ("flow", "empty_arrays", {"stages": []}, "waiting"),
    ("flow", "invalid_type", {"stages": "bad"}, "error"),
    (
        "flow",
        "long_text",
        {
            "origin": "X" * 500,
            "destination": "Y" * 500,
            "eta": "1",
            "stages": [{"name": "ACTIVE", "status": "active"}],
        },
        "ok",
    ),
]


@pytest.mark.parametrize(
    ("panel_type", "case_name", "data", "expected_state"),
    PANEL_CASES,
    ids=[f"{panel}-{case}" for panel, case, _, _ in PANEL_CASES],
)
def test_adversarial_panel_data_renders_without_crashing(
    panel_type, case_name, data, expected_state
) -> None:
    panel = create_panel(panel_type)

    normalized = panel.normalize(data)
    image = panel.render(data, DisplayConfig())

    assert normalized.state == expected_state, case_name
    assert image.size == (400, 300)
    assert image.mode == "L"
    image.close()


@pytest.mark.parametrize(
    ("panel_type", "data"),
    [
        ("progress", {"progress": 50, "tags": []}),
        ("stats", {"primary_value": "1", "breakdown": []}),
        (
            "flow",
            {"stages": [{"name": "ACTIVE", "status": "active"}]},
        ),
    ],
)
def test_each_panel_survives_100_consecutive_renders(panel_type, data) -> None:
    panel = create_panel(panel_type)

    for _ in range(100):
        image = panel.render(data, DisplayConfig())
        assert image.size == (400, 300)
        image.close()
