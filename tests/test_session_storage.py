import json

import pytest

import session_storage


class MemoryStore:
    def __init__(self):
        self.token = None

    def save_token(self, token):
        self.token = token

    def load_token(self):
        return self.token

    def delete_token(self):
        self.token = None


@pytest.fixture
def store(monkeypatch):
    fake_store = MemoryStore()
    monkeypatch.setattr(
        session_storage,
        "_backend",
        lambda: fake_store,
    )
    return fake_store


def test_token_is_replaced_and_removed(tmp_path, store):
    assert session_storage.load_refresh_token(tmp_path) is None

    assert session_storage.save_refresh_token(tmp_path, "first-token")
    assert session_storage.load_refresh_token(tmp_path) == "first-token"

    # A renewed token replaces the one that has already been used.
    assert session_storage.save_refresh_token(tmp_path, "second-token")
    assert session_storage.load_refresh_token(tmp_path) == "second-token"
    assert not session_storage.session_path(tmp_path).exists()

    session_storage.clear_refresh_token(tmp_path)
    assert store.token is None
    assert session_storage.load_refresh_token(tmp_path) is None
    assert session_storage.signed_out_path(tmp_path).exists()

    # Repeating logout is safe.
    session_storage.clear_refresh_token(tmp_path)


def test_old_plaintext_token_is_moved_to_secure_store(tmp_path, store):
    old_file = session_storage.session_path(tmp_path)
    old_file.write_text(
        json.dumps({"refresh_token": "old-token"}),
        encoding="utf-8",
    )
    temporary_file = old_file.with_suffix(".tmp")
    temporary_file.write_text("old-temporary-token", encoding="utf-8")

    assert session_storage.load_refresh_token(tmp_path) == "old-token"
    assert store.token == "old-token"
    assert not old_file.exists()
    assert not temporary_file.exists()


def test_secure_token_takes_priority_over_old_file(tmp_path, store):
    store.token = "current-token"
    old_file = session_storage.session_path(tmp_path)
    old_file.write_text(
        json.dumps({"refresh_token": "outdated-token"}),
        encoding="utf-8",
    )

    assert session_storage.load_refresh_token(tmp_path) == "current-token"
    assert not old_file.exists()


@pytest.mark.parametrize("contents", ["{invalid json", "[]", "{}"])
def test_invalid_old_file_is_removed(tmp_path, store, contents):
    old_file = session_storage.session_path(tmp_path)
    old_file.write_text(contents, encoding="utf-8")

    assert session_storage.load_refresh_token(tmp_path) is None
    assert not old_file.exists()
    assert store.token is None


def test_unavailable_store_never_keeps_plaintext(tmp_path, monkeypatch):
    monkeypatch.setattr(session_storage, "_backend", lambda: None)
    old_file = session_storage.session_path(tmp_path)
    old_file.write_text(
        json.dumps({"refresh_token": "private-token"}),
        encoding="utf-8",
    )

    assert session_storage.load_refresh_token(tmp_path) is None
    assert not old_file.exists()
    assert not session_storage.save_refresh_token(tmp_path, "new-token")
    assert not old_file.exists()


def test_storage_error_does_not_expose_token(tmp_path, monkeypatch, caplog):
    class BrokenStore:
        def load_token(self):
            raise RuntimeError("unavailable")

        def save_token(self, token):
            raise RuntimeError("unavailable")

        def delete_token(self):
            raise RuntimeError("unavailable")

    monkeypatch.setattr(
        session_storage,
        "_backend",
        lambda: BrokenStore(),
    )

    old_file = session_storage.session_path(tmp_path)
    old_file.write_text(
        json.dumps({"refresh_token": "private-token"}),
        encoding="utf-8",
    )

    assert session_storage.load_refresh_token(tmp_path) is None
    assert not old_file.exists()
    assert not session_storage.save_refresh_token(tmp_path, "private-token")

    session_storage.clear_refresh_token(tmp_path)
    assert session_storage.signed_out_path(tmp_path).exists()
    assert "private-token" not in caplog.text


def test_logout_marker_prevents_restoring_old_token(tmp_path, store):
    store.token = "old-token"
    session_storage.signed_out_path(tmp_path).write_text(
        "1",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("system", "module_name"),
    [
        ("win", "desktop_token_store"),
        ("macosx", "desktop_token_store"),
        ("linux", "desktop_token_store"),
        ("android", "android_token_store"),
        ("ios", None),
    ],
)
def test_backend_selection(monkeypatch, system, module_name):
    monkeypatch.setattr(session_storage, "platform", system)

    backend = session_storage._backend()

    if module_name is None:
        assert backend is None
    else:
        assert backend.__name__ == module_name
