def _android_vault():
    from jnius import autoclass

    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    vault = autoclass("org.foodkivy.security.TokenVault")
    return activity, vault


def save_token(token):
    activity, vault = _android_vault()
    vault.save(activity, token)


def load_token():
    activity, vault = _android_vault()
    return vault.load(activity)


def delete_token():
    activity, vault = _android_vault()
    vault.delete(activity)
