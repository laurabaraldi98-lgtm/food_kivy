from session_storage import (
    clear_refresh_token,
    load_refresh_token,
    save_refresh_token,
)


def test_refresh_token_is_replaced_and_removed(tmp_path):
    assert load_refresh_token(tmp_path) is None

    save_refresh_token(tmp_path, "first-token")
    assert load_refresh_token(tmp_path) == "first-token"

    # A renewed token must replace the one that has already been used.
    save_refresh_token(tmp_path, "second-token")
    assert load_refresh_token(tmp_path) == "second-token"

    clear_refresh_token(tmp_path)
    assert load_refresh_token(tmp_path) is None

    # Logging out again should not fail when the file is already gone.
    clear_refresh_token(tmp_path)


def test_corrupt_session_file_is_ignored(tmp_path):
    (tmp_path / "session.json").write_text(
        "{invalid json",
        encoding="utf-8",
    )

    assert load_refresh_token(tmp_path) is None
