import pytest

from language_settings import load_language, save_language


def test_language_is_saved_and_loaded(tmp_path):
    assert load_language(tmp_path) == "it"

    save_language(tmp_path, "en")
    assert load_language(tmp_path) == "en"

    save_language(tmp_path, "it")
    assert load_language(tmp_path) == "it"


def test_language_is_local_to_each_device(tmp_path):
    first_device = tmp_path / "first"
    second_device = tmp_path / "second"
    first_device.mkdir()
    second_device.mkdir()

    save_language(first_device, "en")

    assert load_language(first_device) == "en"
    assert load_language(second_device) == "it"


def test_unknown_saved_language_uses_italian(tmp_path):
    (tmp_path / "language.txt").write_text("fr", encoding="utf-8")

    assert load_language(tmp_path) == "it"


def test_unreadable_saved_language_uses_italian(tmp_path):
    (tmp_path / "language.txt").write_bytes(b"\xff")

    assert load_language(tmp_path) == "it"


def test_unsupported_language_cannot_be_saved(tmp_path):
    with pytest.raises(ValueError, match="Unsupported language: fr"):
        save_language(tmp_path, "fr")

    assert load_language(tmp_path) == "it"
