from requests import RequestException
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from main import FoodApp


@pytest.fixture
def app():
    food_app = FoodApp()
    food_app.session = {
        "access_token": "test-access-token",
        "user": {"id": "user-123"},
    }
    food_app.food = []
    food_app.food_lists = []
    food_app.current_list_id = None
    food_app.current_list_name = ""
    food_app.active_list_label = SimpleNamespace(text="")
    food_app.result = SimpleNamespace(text="")
    food_app.root = SimpleNamespace(current="food")

    return food_app


def test_get_access_token_returns_session_token(app):
    assert app.get_access_token() == "test-access-token"


def test_get_access_token_requires_authentication(app):
    app.session = None

    with pytest.raises(
        RuntimeError,
        match="User is not authenticated",
    ):
        app.get_access_token()


def test_get_user_id_returns_session_user_id(app):
    assert app.get_user_id() == "user-123"


def test_select_food_list_loads_foods_and_updates_labels(app):
    food_list = {
        "id": 7,
        "name": "Preferiti",
    }

    with patch(
        "main.get_foods",
        return_value=["Pasta", "Pizza"],
    ) as mock_get:
        app.select_food_list(food_list)

    mock_get.assert_called_once_with(
        7,
        "test-access-token",
    )

    assert app.current_list_id == 7
    assert app.current_list_name == "Preferiti"
    assert app.food == ["Pasta", "Pizza"]
    assert (
        app.active_list_label.text
        == "Lista attiva: Preferiti"
    )
    assert app.result.text == ""


def test_reload_food_lists_keeps_previous_list_selected(app):
    app.current_list_id = 2

    food_lists = [
        {"id": 1, "name": "I miei cibi"},
        {"id": 2, "name": "Cena"},
    ]

    with (
        patch(
            "main.get_food_lists",
            return_value=food_lists,
        ),
        patch(
            "main.get_foods",
            return_value=["Riso"],
        ) as mock_get_foods,
    ):
        app.reload_food_lists()

    mock_get_foods.assert_called_once_with(
        2,
        "test-access-token",
    )

    assert app.current_list_id == 2
    assert app.current_list_name == "Cena"
    assert app.food == ["Riso"]


def test_reload_food_lists_selects_first_list_when_previous_is_missing(
    app,
):
    app.current_list_id = 99

    food_lists = [
        {"id": 1, "name": "I miei cibi"},
        {"id": 2, "name": "Cena"},
    ]

    with (
        patch(
            "main.get_food_lists",
            return_value=food_lists,
        ),
        patch(
            "main.get_foods",
            return_value=["Pizza"],
        ),
    ):
        app.reload_food_lists()

    assert app.current_list_id == 1
    assert app.current_list_name == "I miei cibi"
    assert app.food == ["Pizza"]


def test_reload_food_lists_clears_active_list_when_no_lists_exist(
    app,
):
    app.current_list_id = 2
    app.current_list_name = "Cena"
    app.food = ["Riso"]
    app.result.text = "Riso"

    with patch(
        "main.get_food_lists",
        return_value=[],
    ):
        app.reload_food_lists()

    assert app.current_list_id is None
    assert app.current_list_name == ""
    assert app.food == []
    assert (
        app.active_list_label.text
        == "Nessuna lista attiva"
    )
    assert app.result.text == ""


def test_choose_food_requires_an_active_list(app):
    app.choose_food(None)

    assert (
        app.result.text
        == "[b]Crea prima una lista[/b]"
    )


def test_choose_food_requires_foods_in_active_list(app):
    app.current_list_id = 1

    app.choose_food(None)

    assert (
        app.result.text
        == "[b]Aggiungi prima qualche cibo[/b]"
    )


def test_choose_food_displays_random_choice(app):
    app.current_list_id = 1
    app.food = ["Pasta", "Pizza"]

    with patch(
        "main.random.choice",
        return_value="Pizza",
    ) as mock_choice:
        app.choose_food(None)

    mock_choice.assert_called_once_with(
        ["Pasta", "Pizza"],
    )

    assert app.result.text == "[b]Pizza[/b]"


def test_logout_invalidates_session_and_returns_to_auth(app):
    app.food_lists = [
        {"id": 1, "name": "I miei cibi"},
    ]
    app.current_list_id = 1
    app.current_list_name = "I miei cibi"
    app.food = ["Pasta"]

    with patch("main.sign_out") as mock_sign_out:
        app.logout()

    mock_sign_out.assert_called_once_with(
        "test-access-token",
    )

    assert app.session is None
    assert app.food_lists == []
    assert app.current_list_id is None
    assert app.food == []
    assert app.root.current == "auth"


def test_get_user_id_requires_authentication(app):
    app.session = None

    with pytest.raises(
        RuntimeError,
        match="User is not authenticated",
    ):
        app.get_user_id()


def test_build_creates_all_screens_and_opens_authentication():
    app = FoodApp()

    manager = app.build()

    assert manager.screen_names == [
        "auth",
        "signup",
        "food",
        "food_lists",
    ]
    assert manager.current == "auth"


def test_open_food_screen_stores_session_loads_lists_and_opens_home(
    app,
):
    session = {
        "access_token": "new-token",
        "user": {"id": "new-user"},
    }

    with patch.object(
        app,
        "reload_food_lists",
    ) as mock_reload:
        app.open_food_screen(session)

    mock_reload.assert_called_once_with()
    assert app.session == session
    assert app.root.current == "food"


def test_open_food_lists_from_menu_closes_menu_and_changes_screen(
    app,
):
    app.menu = SimpleNamespace(dismiss=lambda: None)

    with patch.object(
        app.menu,
        "dismiss",
    ) as mock_dismiss:
        app.open_food_lists_from_menu(None)

    mock_dismiss.assert_called_once_with()
    assert app.root.current == "food_lists"


def test_logout_clears_local_session_when_remote_logout_fails(app):
    with patch(
        "main.sign_out",
        side_effect=RequestException("network error"),
    ):
        app.logout()

    assert app.session is None
    assert app.root.current == "auth"


def test_logout_from_menu_closes_menu_and_logs_out(app):
    app.menu = SimpleNamespace(dismiss=lambda: None)

    with (
        patch.object(
            app.menu,
            "dismiss",
        ) as mock_dismiss,
        patch.object(
            app,
            "logout",
        ) as mock_logout,
    ):
        app.logout_from_menu(None)

    mock_dismiss.assert_called_once_with()
    mock_logout.assert_called_once_with()
