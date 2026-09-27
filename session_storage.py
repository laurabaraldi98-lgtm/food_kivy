import json
import os
from pathlib import Path


def session_path(data_dir):
    return Path(data_dir) / "session.json"


def save_refresh_token(data_dir, refresh_token):
    path = session_path(data_dir)
    temporary_path = path.with_suffix(".tmp")

    temporary_path.write_text(
        json.dumps({"refresh_token": refresh_token}),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def load_refresh_token(data_dir):
    try:
        data = json.loads(
            session_path(data_dir).read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    return data.get("refresh_token")


def clear_refresh_token(data_dir):
    session_path(data_dir).unlink(missing_ok=True)
