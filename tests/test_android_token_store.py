import sys
from types import SimpleNamespace

import pytest

import android_token_store


@pytest.fixture
def fake_android(monkeypatch):
    activity = object()

    class FakeVault:
        saved = None
        deleted = None

        @classmethod
        def save(cls, context, token):
            cls.saved = (context, token)

        @classmethod
        def load(cls, context):
            assert context is activity
            return "stored-token"

        @classmethod
        def delete(cls, context):
            cls.deleted = context

    def autoclass(name):
        if name == "org.kivy.android.PythonActivity":
            return SimpleNamespace(mActivity=activity)
        if name == "org.foodkivy.security.TokenVault":
            return FakeVault
        raise AssertionError(f"Unexpected Java class: {name}")

    # Replace PyJNIus so these tests can run without an Android device.
    monkeypatch.setitem(
        sys.modules,
        "jnius",
        SimpleNamespace(autoclass=autoclass),
    )

    return activity, FakeVault


def test_save_token_calls_android_vault(fake_android):
    activity, vault = fake_android

    android_token_store.save_token("new-token")

    assert vault.saved == (activity, "new-token")


def test_load_token_returns_android_vault_value(fake_android):
    assert android_token_store.load_token() == "stored-token"


def test_delete_token_calls_android_vault(fake_android):
    activity, vault = fake_android

    android_token_store.delete_token()

    assert vault.deleted is activity
