import json
import logging
from pathlib import Path

from kivy.utils import platform

logger = logging.getLogger(__name__)


def session_path(data_dir):
    """Path used by older versions of the app."""
    return Path(data_dir) / "session.json"


def signed_out_path(data_dir):
    return Path(data_dir) / "signed_out"


def _remove_legacy_files(data_dir):
    path = session_path(data_dir)
    path.unlink(missing_ok=True)
    path.with_suffix(".tmp").unlink(missing_ok=True)


def _backend():
    if platform == "android":
        import android_token_store

        return android_token_store

    if platform in ("win", "macosx", "linux"):
        import desktop_token_store

        return desktop_token_store

    return None


def _secure_call(operation, *args):
    try:
        backend = _backend()
        if backend is None:
            return False, None

        result = getattr(backend, operation)(*args)
        return True, result
    except Exception as error:
        # A storage failure must never cause a plaintext fallback.
        logger.warning(
            "Secure token storage failed during %s: %s",
            operation,
            type(error).__name__,
        )
        return False, None


def save_refresh_token(data_dir, refresh_token):
    saved, _ = _secure_call("save_token", refresh_token)
    _remove_legacy_files(data_dir)

    if saved:
        signed_out_path(data_dir).unlink(missing_ok=True)

    return saved


def load_refresh_token(data_dir):
    if signed_out_path(data_dir).exists():
        _remove_legacy_files(data_dir)
        return None

    available, stored_token = _secure_call("load_token")
    if available and stored_token:
        _remove_legacy_files(data_dir)
        return stored_token

    path = session_path(data_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        _remove_legacy_files(data_dir)
        return None

    token = data.get("refresh_token") if isinstance(data, dict) else None
    saved, _ = _secure_call("save_token", token) if token else (False, None)
    _remove_legacy_files(data_dir)

    return token if saved else None


def clear_refresh_token(data_dir):
    # This marker prevents an old vault entry from restoring a logged-out user.
    signed_out_path(data_dir).write_text("1", encoding="utf-8")
    _remove_legacy_files(data_dir)
    _secure_call("delete_token")
