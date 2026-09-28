import pytest

from language_settings import load_language
from main import FoodApp
from translations import TEXTS, translate


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Keep language tests away from the real app preferences.
    monkeypatch.setattr(
        FoodApp,
        "user_data_dir",
        property(lambda self: str(tmp_path)),
    )

    food_app = FoodApp()
    food_app.root = food_app.build()
    return food_app


def test_italian_and_english_have_the_same_keys():
    assert TEXTS["it"].keys() == TEXTS["en"].keys()


def test_translation_keeps_the_user_list_name():
    assert translate("en", "active_list", name="Cena") == (
        "Active list: Cena"
    )


def test_language_button_changes_home_and_can_switch_back(app):
    app.toggle_language(None)

    assert app.language == "en"
    assert app.title_label.text == "What should we eat?"
    assert app.choose_button.text == "Choose for me"
    assert app.lists_button.text == "Manage lists"
    assert app.logout_button.text == "Log out"
    assert app.language_button.text == "Italiano"
    assert app.active_list_label.text == "No active list"
    assert load_language(app.user_data_dir) == "en"

    app.toggle_language(None)

    assert app.language == "it"
    assert app.title_label.text == "Cosa mangiamo?"
    assert app.choose_button.text == "Scegli per me"
    assert app.language_button.text == "English"
    assert load_language(app.user_data_dir) == "it"


def test_saved_language_is_loaded_when_app_restarts(app):
    app.set_language("en")

    restarted_app = FoodApp()
    restarted_app.root = restarted_app.build()

    assert restarted_app.language == "en"
    assert restarted_app.title_label.text == "What should we eat?"
    assert restarted_app.language_button.text == "Italiano"

    auth_screen = restarted_app.root.get_screen("auth")
    assert auth_screen.sign_in_button.text == "Sign in"
    assert auth_screen.language_button.text == "Italiano"

    signup_screen = restarted_app.root.get_screen("signup")
    assert signup_screen.title_label.text == "Create account"
    assert signup_screen.language_button.text == "Italiano"


def test_active_list_name_is_not_translated(app):
    app.current_list_id = 7
    app.current_list_name = "Cena"

    app.set_language("en")

    assert app.active_list_label.text == "Active list: Cena"


def test_messages_change_language_but_food_name_does_not(app):
    app.choose_food(None)
    app.set_language("en")
    assert app.result.text == "[b]Create a list first[/b]"

    app.current_list_id = 7
    app.choose_food(None)
    assert app.result.text == "[b]Add some food first[/b]"

    app.set_language("it")
    assert app.result.text == "[b]Aggiungi prima qualche cibo[/b]"

    app.food = ["Pizza"]
    app.choose_food(None)
    app.set_language("en")
    assert app.result.text == "[b]Pizza[/b]"


def test_unsupported_language_is_rejected(app):
    with pytest.raises(ValueError, match="Unsupported language: fr"):
        app.set_language("fr")

    assert app.language == "it"
    assert load_language(app.user_data_dir) == "it"
