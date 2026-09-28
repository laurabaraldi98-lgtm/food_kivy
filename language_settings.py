from pathlib import Path

from translations import TEXTS


DEFAULT_LANGUAGE = "it"


def language_path(data_dir):
    return Path(data_dir) / "language.txt"


def load_language(data_dir):
    try:
        language = language_path(data_dir).read_text(
            encoding="utf-8"
        ).strip()
    except (OSError, UnicodeError):
        return DEFAULT_LANGUAGE

    return language if language in TEXTS else DEFAULT_LANGUAGE


def save_language(data_dir, language):
    if language not in TEXTS:
        raise ValueError(f"Unsupported language: {language}")

    language_path(data_dir).write_text(
        language,
        encoding="utf-8",
    )
