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
from food_list_popups import add_colored_background


def test_add_colored_background_tracks_widget_size_and_position():
    widget = BoxLayout()

    add_colored_background(widget)
    widget.size = (200, 100)
    widget.pos = (10, 20)


def test_create_popup_requires_name(screen, fake_popup):
    app = make_app()

    with patch("food_list_popups.App.get_running_app", return_value=app):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup.opened
    assert popup_status(popup).text == "Inserisci un nome per la lista"


def test_create_popup_rejects_duplicate_name(screen, fake_popup):
    app = make_app(food_lists=[{"id": 1, "name": " Cena "}])

    with patch("food_list_popups.App.get_running_app", return_value=app):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "cena"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup_status(popup).text == "Esiste già una lista con questo nome"


def test_create_popup_displays_request_error(screen, fake_popup):
    app = make_app()

    with (
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.create_food_list",
              side_effect=RequestException),
    ):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Cena"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup_status(popup).text == "Impossibile creare la lista"


def test_create_popup_creates_and_selects_list(screen, fake_popup):
    app = make_app()
    created = {"id": 3, "name": "Cena"}

    with (
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch(
            "food_list_popups.create_food_list",
            return_value=created,
        ) as mock_create,
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "  Cena  "
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    mock_create.assert_called_once_with("Cena", "user-123", "test-token")
    assert app.food_lists == [created]
    app.select_food_list.assert_called_once_with(created)
    assert popup.dismissed
    mock_render.assert_called_once_with()


def test_rename_popup_does_nothing_without_selection(screen, fake_popup):
    with patch.object(screen, "get_selected_list", return_value=None):
        screen.open_rename_popup(None)

    assert fake_popup.last is None


@pytest.mark.parametrize(
    ("new_name", "food_lists", "expected_message"),
    [
        ("   ", [], "Inserisci un nuovo nome"),
        (
            "cena",
            [
                {"id": 1, "name": "Pranzo"},
                {"id": 2, "name": " Cena "},
            ],
            "Esiste già una lista con questo nome",
        ),
    ],
)
def test_rename_popup_validates_name(
    screen,
    fake_popup,
    new_name,
    food_lists,
    expected_message,
):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=food_lists or [selected])

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = new_name
        find_widget(popup.content, RoundedButton,
                    text="Salva").dispatch("on_release")

    assert popup_status(popup).text == expected_message


def test_rename_popup_displays_request_error(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=[selected])

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.rename_food_list",
              side_effect=RequestException),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Cena"
        find_widget(popup.content, RoundedButton,
                    text="Salva").dispatch("on_release")

    assert popup_status(popup).text == "Impossibile rinominare la lista"


def test_rename_popup_updates_active_list(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=[selected], current_list_id=1)

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.rename_food_list") as mock_rename,
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "  Cena  "
        find_widget(popup.content, RoundedButton,
                    text="Salva").dispatch("on_release")

    mock_rename.assert_called_once_with(1, "Cena", "test-token")
    assert selected["name"] == "Cena"
    assert app.current_list_name == "Cena"
    assert app.active_list_label.text == "Lista attiva: Cena"
    assert popup.dismissed
    mock_render.assert_called_once_with()


def test_delete_popup_does_nothing_without_selection(screen, fake_popup):
    with patch.object(screen, "get_selected_list", return_value=None):
        screen.open_delete_popup(None)

    assert fake_popup.last is None


def test_delete_popup_displays_request_error(screen, fake_popup):
    selected = {"id": 1, "name": "Cena"}
    app = make_app(food_lists=[selected], current_list_id=1)

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.delete_food_list",
              side_effect=RequestException),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    message = find_widget(popup.content, Label)
    assert message.text == "Impossibile eliminare la lista"


def test_delete_popup_selects_next_list(screen, fake_popup):
    selected = {"id": 1, "name": "Cena"}
    remaining = {"id": 2, "name": "Pranzo"}
    app = make_app(
        food_lists=[selected, remaining],
        current_list_id=1,
    )

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.delete_food_list") as mock_delete,
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    mock_delete.assert_called_once_with(1, "test-token")
    assert app.food_lists == [remaining]
    app.select_food_list.assert_called_once_with(remaining)
    assert screen.selected_list_id is None
    assert popup.dismissed
    mock_render.assert_called_once_with()


def test_delete_popup_clears_active_list_when_last_list_is_deleted(
    screen,
    fake_popup,
):
    selected = {"id": 1, "name": "Cena"}
    app = make_app(food_lists=[selected], current_list_id=1)

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.delete_food_list"),
        patch.object(screen, "render_lists"),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    assert app.food_lists == []
    app.clear_active_food_list.assert_called_once_with()


def test_create_shared_list(screen, fake_popup):
    app = make_app()
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    created = {"id": 3, "name": "Famiglia", "group_id": 9}

    with (
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.create_group", return_value=group) as create_group,
        patch(
            "food_list_popups.create_group_food_list", return_value=created
        ) as create_list,
        patch.object(screen, "render_lists") as render,
    ):
        screen.open_create_popup(None, shared=True)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "  Famiglia  "
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    create_group.assert_called_once_with("Famiglia", "user-123", "test-token")
    create_list.assert_called_once_with("Famiglia", 9, "test-token")
    assert screen.groups == [group]
    assert app.food_lists == [created]
    assert screen.selected_list_id == 3
    assert popup.dismissed
    render.assert_called_once_with()


def test_create_shared_list_reports_group_error(screen, fake_popup):
    app = make_app()

    with (
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.create_group", side_effect=RequestException),
    ):
        screen.open_create_popup(None, shared=True)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Famiglia"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup_status(popup).text == "Impossibile creare la lista"


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_create_shared_list_removes_orphan_group(
    screen, fake_popup, cleanup_fails
):
    app = make_app()
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    cleanup_error = RequestException if cleanup_fails else None

    with (
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.create_group", return_value=group),
        patch("food_list_popups.create_group_food_list",
              side_effect=RequestException),
        patch("food_list_popups.delete_group", side_effect=cleanup_error) as cleanup,
    ):
        screen.open_create_popup(None, shared=True)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Famiglia"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    cleanup.assert_called_once_with(9, "test-token")
    assert popup_status(popup).text == "Impossibile creare la lista"


def test_rename_shared_list_updates_group(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    app = make_app(food_lists=[selected])
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.rename_food_list") as rename_list,
        patch("food_list_popups.rename_group") as rename_group,
        patch.object(screen, "render_lists"),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Amici"
        find_widget(popup.content, RoundedButton,
                    text="Salva").dispatch("on_release")

    rename_list.assert_called_once_with(1, "Amici", "test-token")
    rename_group.assert_called_once_with(9, "Amici", "test-token")
    assert selected["name"] == group["name"] == "Amici"


def test_rename_shared_list_reports_group_error(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    app = make_app(food_lists=[selected])
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.rename_food_list"),
        patch("food_list_popups.rename_group", side_effect=RequestException),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Amici"
        find_widget(popup.content, RoundedButton,
                    text="Salva").dispatch("on_release")

    assert popup_status(popup).text == "Impossibile rinominare la lista"


def test_delete_shared_list_shows_warning_and_deletes_group(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    app = make_app(food_lists=[selected], current_list_id=1)
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.delete_group") as delete,
        patch.object(screen, "render_lists"),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        warning = find_widget(popup.content, Label)
        assert "Tutti i membri perderanno l'accesso" in warning.text
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    delete.assert_called_once_with(9, "test-token")
    assert screen.groups == []
    assert app.food_lists == []


def test_delete_shared_list_reports_error(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    app = make_app(food_lists=[selected])
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.delete_group", side_effect=RequestException),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    assert find_widget(
        popup.content, Label).text == "Impossibile eliminare la lista"


def test_leave_popup_handles_missing_selection_or_group(screen, fake_popup):
    with patch.object(screen, "get_selected_list", return_value=None):
        screen.open_leave_popup(None)
    assert fake_popup.last is None

    selected = {"id": 1, "name": "Famiglia", "group_id": 99}
    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch.object(screen, "get_group_for_list", return_value=None),
    ):
        screen.open_leave_popup(None)
    assert screen.status_label.text == "Impossibile abbandonare la lista condivisa"


def test_leave_popup_reports_request_error(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "other-user"}
    app = make_app(food_lists=[selected], current_list_id=1)

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch.object(screen, "get_group_for_list", return_value=group),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.remove_group_member",
              side_effect=RequestException),
    ):
        screen.open_leave_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Abbandona").dispatch("on_release")

    assert find_widget(
        popup.content, Label).text == "Impossibile abbandonare la lista"


@pytest.mark.parametrize("has_remaining", [False, True])
def test_leave_shared_list(screen, fake_popup, has_remaining):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "other-user"}
    remaining = {"id": 2, "name": "Personale"}
    lists = [selected, remaining] if has_remaining else [selected]
    app = make_app(food_lists=lists, current_list_id=1)
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch.object(screen, "get_group_for_list", return_value=group),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.remove_group_member") as remove,
        patch.object(screen, "render_lists"),
    ):
        screen.open_leave_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Abbandona").dispatch("on_release")

    remove.assert_called_once_with(9, "user-123", "test-token")
    assert selected not in app.food_lists
    assert screen.groups == []
    if has_remaining:
        app.select_food_list.assert_called_once_with(remaining)
    else:
        app.clear_active_food_list.assert_called_once_with()


@pytest.mark.parametrize(
    ("shared", "expected_title", "expected_hint"),
    [
        (False, "Create personal list", "Personal list name"),
        (True, "Create shared list", "Shared list name"),
    ],
)
def test_create_popup_uses_english(
    screen, fake_popup, shared, expected_title, expected_hint
):
    app = make_app()
    screen.refresh_texts("en")

    with patch("food_list_popups.App.get_running_app", return_value=app):
        screen.open_create_popup(None, shared=shared)
        popup = fake_popup.last

        assert popup.title == expected_title
        assert find_widget(popup.content, TextInput).hint_text == expected_hint

        create_button = find_widget(
            popup.content, RoundedButton, text="Create"
        )
        create_button.dispatch("on_release")

    assert popup_status(popup).text == "Enter a name for the list"


def test_rename_popup_uses_english_and_updates_active_label(
    screen, fake_popup
):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=[selected], current_list_id=1)
    screen.refresh_texts("en")

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch("food_list_popups.rename_food_list"),
        patch.object(screen, "render_lists"),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last

        assert popup.title == "Rename list"
        assert find_widget(popup.content, TextInput).text == "Pranzo"

        find_widget(popup.content, TextInput).text = "Dinner"
        find_widget(
            popup.content, RoundedButton, text="Save"
        ).dispatch("on_release")

    assert selected["name"] == "Dinner"
    assert app.active_list_label.text == "Active list: Dinner"


def test_rename_popup_shows_english_validation_error(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=[selected])
    screen.refresh_texts("en")

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
    ):
        screen.open_rename_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "   "
        find_widget(
            popup.content, RoundedButton, text="Save"
        ).dispatch("on_release")

    assert popup_status(popup).text == "Enter a new name"


@pytest.mark.parametrize(
    ("shared", "expected_text"),
    [
        (False, "Delete the list 'Pranzo'?"),
        (True, "Delete the shared list 'Pranzo'?"),
    ],
)
def test_delete_popup_uses_english(
    screen, fake_popup, shared, expected_text
):
    selected = {"id": 1, "name": "Pranzo"}
    if shared:
        selected["group_id"] = 9

    screen.refresh_texts("en")

    with patch.object(
        screen, "get_selected_list", return_value=selected
    ):
        screen.open_delete_popup(None)

    popup = fake_popup.last
    message = find_widget(popup.content, Label)

    assert popup.title == "Confirm deletion"
    assert expected_text in message.text
    assert "Pranzo" in message.text
    find_widget(popup.content, RoundedButton, text="Cancel")
    find_widget(popup.content, RoundedButton, text="Delete")


def test_delete_popup_shows_english_request_error(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo"}
    app = make_app(food_lists=[selected], current_list_id=1)
    screen.refresh_texts("en")

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch(
            "food_list_popups.delete_food_list",
            side_effect=RequestException,
        ),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(
            popup.content, RoundedButton, text="Delete"
        ).dispatch("on_release")

    assert find_widget(popup.content, Label).text == (
        "Could not delete the list"
    )


def test_leave_popup_uses_english_and_wraps_message(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo", "group_id": 9}
    group = {"id": 9, "name": "Pranzo", "owner_id": "other-user"}
    screen.refresh_texts("en")

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch.object(screen, "get_group_for_list", return_value=group),
    ):
        screen.open_leave_popup(None)

    popup = fake_popup.last
    message = find_widget(popup.content, Label)
    message.width = 200

    assert popup.title == "Leave shared list"
    assert "Leave the list 'Pranzo'?" in message.text
    assert message.text_size[0] == 200
    find_widget(popup.content, RoundedButton, text="Cancel")
    find_widget(popup.content, RoundedButton, text="Leave")


def test_leave_popup_shows_english_request_error(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo", "group_id": 9}
    group = {"id": 9, "name": "Pranzo", "owner_id": "other-user"}
    app = make_app(food_lists=[selected], current_list_id=1)
    screen.refresh_texts("en")

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch.object(screen, "get_group_for_list", return_value=group),
        patch("food_list_popups.App.get_running_app", return_value=app),
        patch(
            "food_list_popups.remove_group_member",
            side_effect=RequestException,
        ),
    ):
        screen.open_leave_popup(None)
        popup = fake_popup.last
        find_widget(
            popup.content, RoundedButton, text="Leave"
        ).dispatch("on_release")

    assert find_widget(popup.content, Label).text == (
        "Could not leave the list"
    )


def test_delete_popup_wraps_message(screen, fake_popup):
    selected = {"id": 1, "name": "Pranzo"}

    with patch.object(
        screen, "get_selected_list", return_value=selected
    ):
        screen.open_delete_popup(None)

    message = find_widget(fake_popup.last.content, Label)
    message.width = 200

    assert message.text_size[0] == 200
