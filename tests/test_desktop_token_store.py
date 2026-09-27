import sys
from types import SimpleNamespace

import pytest

import desktop_token_store


class FakeVault:
    def __init__(self):
        self.passwords = {}

    def set_password(self, service, account, password):
        self.passwords[(service, account)] = password

    def get_password(self, service, account):
        return self.passwords.get((service, account))

    def delete_password(self, service, account):
        del self.passwords[(service, account)]


class WindowsVault(FakeVault):
    pass


class MacVault(FakeVault):
    pass


class SecretServiceVault(FakeVault):
    pass


class KWalletVault(FakeVault):
    pass


@pytest.fixture
def fake_backends(monkeypatch):
    # Replace operating-system backends without accessing real credentials.
    monkeypatch.setitem(
        sys.modules,
        "keyring.backends.Windows",
        SimpleNamespace(WinVaultKeyring=WindowsVault),
    )
    monkeypatch.setitem(
        sys.modules,
        "keyring.backends.macOS",
        SimpleNamespace(Keyring=MacVault),
    )
    monkeypatch.setitem(
        sys.modules,
        "keyring.backends.SecretService",
        SimpleNamespace(Keyring=SecretServiceVault),
    )
    monkeypatch.setitem(
        sys.modules,
        "keyring.backends.kwallet",
        SimpleNamespace(DBusKeyring=KWalletVault),
    )


@pytest.mark.parametrize(
    ("platform", "vault_class"),
    [
        ("win", WindowsVault),
        ("macosx", MacVault),
        ("linux", SecretServiceVault),
        ("linux", KWalletVault),
    ],
)
def test_accepts_supported_vaults(
    monkeypatch, fake_backends, platform, vault_class
):
    vault = vault_class()
    monkeypatch.setattr(desktop_token_store, "platform", platform)
    monkeypatch.setattr(
        desktop_token_store.keyring,
        "get_keyring",
        lambda: vault,
    )

    assert desktop_token_store.get_secure_vault() is vault


def test_rejects_unsupported_vault(monkeypatch, fake_backends):
    monkeypatch.setattr(desktop_token_store, "platform", "win")
    monkeypatch.setattr(
        desktop_token_store.keyring,
        "get_keyring",
        lambda: FakeVault(),
    )

    with pytest.raises(
        RuntimeError,
        match="No supported secure credential store",
    ):
        desktop_token_store.get_secure_vault()


def test_rejects_unsupported_platform(monkeypatch, fake_backends):
    monkeypatch.setattr(desktop_token_store, "platform", "android")
    monkeypatch.setattr(
        desktop_token_store.keyring,
        "get_keyring",
        lambda: FakeVault(),
    )

    with pytest.raises(RuntimeError, match="Unsupported desktop platform"):
        desktop_token_store.get_secure_vault()


def test_save_load_and_delete_token(monkeypatch, fake_backends):
    vault = WindowsVault()
    monkeypatch.setattr(desktop_token_store, "platform", "win")
    monkeypatch.setattr(
        desktop_token_store.keyring,
        "get_keyring",
        lambda: vault,
    )

    desktop_token_store.save_token("test-token")
    assert desktop_token_store.load_token() == "test-token"

    desktop_token_store.delete_token()
    assert desktop_token_store.load_token() is None


def test_delete_missing_token_does_nothing(monkeypatch, fake_backends):
    vault = WindowsVault()
    monkeypatch.setattr(desktop_token_store, "platform", "win")
    monkeypatch.setattr(
        desktop_token_store.keyring,
        "get_keyring",
        lambda: vault,
    )

    desktop_token_store.delete_token()

    assert vault.passwords == {}
