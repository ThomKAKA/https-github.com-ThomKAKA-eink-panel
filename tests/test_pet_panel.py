"""Deterministic pet page rendering and daily state derivation."""

from __future__ import annotations

import io

import pytest
from pydantic import ValidationError

from panels.base import DisplayConfig
from panels.frame_converter import png_to_logical_raw
from panels.pet import PetPageData, PetPanel, pet_state
from panels.transport_adapter import logical_to_transport


def document(**overrides) -> dict:
    payload = {
        "revision": 2,
        "updated_at": "2026-11-08 12:05",
        "day_key": "2026-11-08",
        "name": "大肥鱼",
        "satiety": 50,
        "mood": 60,
        "affinity": 0,
        "last_fed": "2026-11-08",
        "last_interaction": "2026-11-08 12:05",
    }
    payload.update(overrides)
    return payload


def render(data: dict) -> bytes:
    image = PetPanel().render(data, DisplayConfig(), "eink", strict=True)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def image_of(data: dict):
    return PetPanel().render(data, DisplayConfig(), "eink", strict=True)


def texts_of(image) -> list[str]:
    return [entry["text"] for entry in image.info["render_audit"]["texts"]]


def sizes_of(image) -> dict[str, int]:
    return {entry["text"]: entry["size"] for entry in image.info["render_audit"]["texts"]}


def test_metadata_describes_the_pet_panel():
    metadata = PetPanel().get_metadata()

    assert metadata.panel_type == "pet"
    assert metadata.display_name == "PetPanel"


def test_document_rejects_unknown_and_out_of_range_fields():
    with pytest.raises(ValidationError):
        PetPageData.model_validate(document(kind="fish"))
    with pytest.raises(ValidationError):
        PetPageData.model_validate(document(satiety=101))
    with pytest.raises(ValidationError):
        PetPageData.model_validate(document(affinity=1000))
    with pytest.raises(ValidationError):
        PetPageData.model_validate(document(name="九个字的名字太长了"))
    with pytest.raises(ValidationError):
        PetPageData.model_validate(document(last_fed="2026/11/08"))


def test_render_is_byte_deterministic_and_exactly_one_transport_frame():
    first = render(document())
    second = render(document())

    assert first == second
    assert len(logical_to_transport(png_to_logical_raw(first))) == 15000


def test_render_shows_name_level_bars_and_today_state():
    image = image_of(document())
    texts = texts_of(image)
    sizes = sizes_of(image)

    assert "宠物" in texts
    assert "PET" in texts
    assert "大肥鱼" in texts
    assert "Lv.1" in texts
    for label in ("饱食", "心情", "亲密"):
        assert label in texts
        assert sizes[label] == 10
    assert "今天已喂" in texts
    assert "上次互动 11-08 12:05" in texts
    assert "来源 / pet r2" in texts
    assert sizes["来源 / pet r2"] == 10
    assert "更新 / 2026-11-08 12:05" in texts
    assert sizes["大肥鱼"] == 18


def test_render_distinguishes_fed_and_unfed():
    fed = texts_of(image_of(document()))
    unfed = texts_of(image_of(document(last_fed=None)))
    prefix = texts_of(image_of(document(updated_at=None, last_interaction=None, last_fed=None)))

    assert "今天已喂" in fed
    assert "今天还没喂" in unfed
    assert "今天还没喂" in prefix
    assert any("等待互动" in text for text in prefix)


def test_render_changes_with_mood_and_satiety():
    happy = render(document(mood=80))
    low = render(document(mood=20))
    full = render(document(satiety=70))
    hungry = render(document(satiety=0))

    assert happy != low
    assert full != hungry


def test_same_day_costs_nothing_and_each_day_decays_more():
    same = pet_state(PetPageData.model_validate(document()), "2026-11-08")
    next_day = pet_state(PetPageData.model_validate(document()), "2026-11-09")
    three_days = pet_state(PetPageData.model_validate(document()), "2026-11-11")

    assert same.satiety == 50
    assert next_day.satiety == 25
    assert three_days.satiety == 0


def test_hunger_reduces_mood_and_state_labels_track_boundaries():
    hungry = pet_state(PetPageData.model_validate(document()), "2026-11-09")
    fed = pet_state(PetPageData.model_validate(document()), "2026-11-08")

    assert hungry.mood == 50
    assert fed.mood == 60
    assert fed.satiety_label == "正常"
    assert fed.mood_label == "一般"

    assert pet_state(PetPageData.model_validate(document(satiety=70)), "2026-11-08").satiety_label == "很饱"
    assert pet_state(PetPageData.model_validate(document(satiety=1)), "2026-11-08").satiety_label == "有点饿"
    assert pet_state(PetPageData.model_validate(document(satiety=0)), "2026-11-08").satiety_label == "饿扁了"
    assert pet_state(PetPageData.model_validate(document(mood=70)), "2026-11-08").mood_label == "开心"
    assert pet_state(PetPageData.model_validate(document(mood=39)), "2026-11-08").mood_label == "低落"


def test_level_grows_with_affinity():
    def level(affinity: int) -> int:
        return pet_state(PetPageData.model_validate(document(affinity=affinity)), "2026-11-08").level

    assert level(0) == 1
    assert level(24) == 1
    assert level(25) == 2
    assert level(50) == 3
    assert level(999) == 40


def test_fed_today_is_compared_with_the_render_day():
    fed = pet_state(PetPageData.model_validate(document()), "2026-11-08")
    unfed = pet_state(PetPageData.model_validate(document()), "2026-11-09")

    assert fed.fed_today is True
    assert unfed.fed_today is False
