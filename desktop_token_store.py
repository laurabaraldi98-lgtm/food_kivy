import keyring
from kivy.utils import platform

SERVICE = "food-kivy-app"
ACCOUNT = "supabase-refresh-token"


def get_secure_vault():
    """Return a supported operating-system credential store."""
    vault = keyring.get_keyring()

    if platform == "win":
        from keyring.backends.Windows import WinVaultKeyring

        supported = (WinVaultKeyring,)
    elif platform == "macosx":
        from keyring.backends.macOS import Keyring as MacOSKeyring

        supported = (MacOSKeyring,)
    elif platform == "linux":
        from keyring.backends.SecretService import Keyring as SecretServiceKeyring
        from keyring.backends.kwallet import DBusKeyring

        supported = (SecretServiceKeyring, DBusKeyring)
    else:
        raise RuntimeError(f"Unsupported desktop platform: {platform}")

    if type(vault) not in supported:
        raise RuntimeError(
            "No supported secure credential store is available"
        )

    return vault


def save_token(token):
    get_secure_vault().set_password(SERVICE, ACCOUNT, token)


def load_token():
    return get_secure_vault().get_password(SERVICE, ACCOUNT)


def delete_token():
    vault = get_secure_vault()

    if vault.get_password(SERVICE, ACCOUNT) is not None:
        vault.delete_password(SERVICE, ACCOUNT)
