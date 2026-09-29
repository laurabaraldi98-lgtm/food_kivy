from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from requests import RequestException

from ui_components import RoundedButton
from food_lists_test_helpers import (
    FakePopup,
    fake_popup,
    find_widget,
    make_app,
    popup_status,
    screen,
)


def test_on_pre_enter_reloads_and_renders_lists(screen):
    app = make_app()
    groups = [{"id": 9, "name": "Famiglia", "owner_id": "user-123"}]

    with (
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.get_groups", return_value=groups),
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.selected_list_id = 4
        screen.status_label.text = "Errore precedente"
        screen.on_pre_enter()

    app.reload_food_lists.assert_called_once_with()
    assert screen.groups == groups
    assert screen.status_label.text == ""
    assert screen.selected_list_id is None
    mock_render.assert_called_once_with()


def test_on_pre_enter_displays_loading_error(screen):
    app = make_app()
    app.reload_food_lists.side_effect = RequestException

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.on_pre_enter()

    assert screen.status_label.text == "Impossibile caricare le liste"


def test_render_lists_displays_empty_message(screen):
    app = make_app()

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    message = find_widget(
        screen.list_container,
        Label,
        text="Non hai ancora nessuna lista",
    )

    assert message.text == "Non hai ancora nessuna lista"


def test_render_lists_marks_active_list_and_shows_selected_actions(screen):
    app = make_app(
        food_lists=[
            {"id": 1, "name": "I miei cibi"},
            {"id": 2, "name": "Cena"},
        ],
        current_list_id=1,
    )
    screen.selected_list_id = 2

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    button_texts = {
        widget.text
        for widget in screen.list_container.walk()
        if isinstance(widget, RoundedButton)
    }

    assert "*  I miei cibi" in button_texts
    assert "Cena" in button_texts
    assert {"Vedi cibi", "Rinomina", "Elimina"} <= button_texts


def test_clicking_rendered_list_selects_it(screen):
    food_list = {"id": 2, "name": "Cena"}
    app = make_app(food_lists=[food_list])

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

        button = find_widget(
            screen.list_container,
            RoundedButton,
            text="Cena",
        )
        button.dispatch("on_release")

    app.select_food_list.assert_called_once_with(food_list)
    assert screen.selected_list_id == 2


def test_select_list_collapses_list_that_is_already_selected(screen):
    food_list = {"id": 2, "name": "Cena"}
    app = make_app(food_lists=[food_list])
    screen.selected_list_id = 2

    with (
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.select_list(food_list)

    assert screen.selected_list_id is None
    app.select_food_list.assert_not_called()
    mock_render.assert_called_once_with()


def test_select_list_displays_error_when_foods_cannot_be_loaded(screen):
    food_list = {"id": 2, "name": "Cena"}
    app = make_app(food_lists=[food_list])
    app.select_food_list.side_effect = RequestException

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.select_list(food_list)

    assert screen.selected_list_id is None
    assert screen.status_label.text == "Impossibile caricare i cibi"


def test_get_selected_list_returns_matching_list(screen):
    selected = {"id": 2, "name": "Cena"}
    app = make_app(
        food_lists=[
            {"id": 1, "name": "Pranzo"},
            selected,
        ]
    )
    screen.selected_list_id = 2

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        result = screen.get_selected_list()

    assert result == selected


def test_get_selected_list_returns_none_without_selection(screen):
    app = make_app(food_lists=[{"id": 1, "name": "Pranzo"}])

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        result = screen.get_selected_list()

    assert result is None


def test_open_selected_foods_does_nothing_without_selection(screen):
    with (
        patch.object(screen, "get_selected_list", return_value=None),
        patch("food_lists_screen.show_food_popup") as mock_show,
    ):
        screen.open_selected_foods(None)

    mock_show.assert_not_called()


def test_open_selected_foods_opens_food_popup(screen):
    app = make_app()

    with (
        patch.object(
            screen,
            "get_selected_list",
            return_value={"id": 1, "name": "Cena"},
        ),
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.show_food_popup") as mock_show,
    ):
        screen.open_selected_foods(None)

    mock_show.assert_called_once_with(app)


def test_go_home_from_menu_closes_menu_and_changes_screen(screen):
    app = make_app()
    screen.menu = SimpleNamespace(dismiss=Mock())

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.go_home_from_menu(None)

    screen.menu.dismiss.assert_called_once_with()
    assert app.root.current == "food"


def test_logout_from_menu_closes_menu_and_logs_out(screen):
    app = make_app()
    screen.menu = SimpleNamespace(dismiss=Mock())

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.logout_from_menu(None)

    screen.menu.dismiss.assert_called_once_with()
    app.logout.assert_called_once_with()


def test_render_shared_list_for_owner(screen):
    shared = {"id": 2, "name": "Famiglia", "group_id": 9}
    app = make_app(food_lists=[shared], current_list_id=2)
    screen.groups = [{"id": 9, "name": "Famiglia", "owner_id": "user-123"}]
    screen.selected_list_id = 2

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    texts = {
        widget.text
        for widget in screen.list_container.walk()
        if isinstance(widget, RoundedButton)
    }
    assert "*  Famiglia  (condivisa)" in texts
    assert {"Vedi cibi", "Membri", "Rinomina", "Elimina"} <= texts
    assert "Abbandona" not in texts


def test_render_shared_list_for_member(screen):
    shared = {"id": 2, "name": "Famiglia", "group_id": 9}
    app = make_app(food_lists=[shared])
    screen.groups = [{"id": 9, "name": "Famiglia", "owner_id": "other-user"}]
    screen.selected_list_id = 2

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    texts = {
        widget.text
        for widget in screen.list_container.walk()
        if isinstance(widget, RoundedButton)
    }
    assert "Famiglia  (condivisa)" in texts
    assert "Abbandona" in texts
    assert "Elimina" not in texts


def test_get_group_for_list(screen):
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    screen.groups = [group]

    assert screen.get_group_for_list({"id": 1, "name": "Personale"}) is None
    assert screen.get_group_for_list(
        {"id": 2, "name": "Famiglia", "group_id": 9}
    ) == group
    assert screen.get_group_for_list(
        {"id": 3, "name": "Sconosciuta", "group_id": 99}
    ) is None


def test_open_members_popup_handles_missing_selection_or_group(screen):
    with patch("food_lists_screen.show_group_members_popup") as show:
        with patch.object(screen, "get_selected_list", return_value=None):
            screen.open_members_popup(None)
        show.assert_not_called()

        with (
            patch.object(
                screen,
                "get_selected_list",
                return_value={"id": 2, "name": "Famiglia", "group_id": 99},
            ),
            patch.object(screen, "get_group_for_list", return_value=None),
        ):
            screen.open_members_popup(None)

    assert screen.status_label.text == "Impossibile aprire i membri della lista"


def test_open_members_popup(screen):
    food_list = {"id": 2, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}

    with (
        patch.object(screen, "get_selected_list", return_value=food_list),
        patch.object(screen, "get_group_for_list", return_value=group),
        patch("food_lists_screen.show_group_members_popup") as show,
    ):
        screen.open_members_popup(None)

    show.assert_called_once_with(group)
    assert screen.status_label.text == ""


def test_refresh_texts_translates_list_screen_controls(screen):
    screen.refresh_texts("en")

    assert screen.title_label.text == "My lists"
    assert screen.home_button.text == "Back to Home"
    assert screen.personal_button.text == "+ Personal"
    assert screen.shared_button.text == "+ Shared"
    assert screen.logout_button.text == "Log out"
    assert screen.language_button.text == "Italiano"

    screen.refresh_texts("it")

    assert screen.title_label.text == "Le mie liste"
    assert screen.language_button.text == "English"


def test_render_lists_translates_actions_but_keeps_list_name(screen):
    food_list = {"id": 2, "name": "Pranzo", "group_id": 9}
    app = make_app(food_lists=[food_list], current_list_id=2)
    screen.groups = [
        {"id": 9, "name": "Pranzo", "owner_id": "other-user"}
    ]
    screen.selected_list_id = 2
    screen.refresh_texts("en")

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    texts = {
        widget.text
        for widget in screen.list_container.walk()
        if isinstance(widget, RoundedButton)
    }

    assert "*  Pranzo  (shared)" in texts
    assert {"View foods", "Members", "Rename", "Leave"} <= texts
    assert "Delete" not in texts


def test_empty_lists_message_is_translated(screen):
    app = make_app()
    screen.refresh_texts("en")

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.render_lists()

    find_widget(
        screen.list_container,
        Label,
        text="You don't have any lists yet",
    )


def test_language_button_requests_change_from_app(screen):
    app = SimpleNamespace(language="it", set_language=Mock())
    screen.menu = SimpleNamespace(dismiss=Mock())

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.toggle_language(None)

    screen.menu.dismiss.assert_called_once_with()
    app.set_language.assert_called_once_with("en")
