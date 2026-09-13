from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from requests import RequestException

from food_lists_screen import FoodListsScreen, add_colored_background
from ui_components import RoundedButton


class FakePopup:
    last = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.opened = False
        self.dismissed = False
        FakePopup.last = self

    def open(self):
        self.opened = True

    def dismiss(self, *args):
        self.dismissed = True


@pytest.fixture
def screen():
    return FoodListsScreen(name="food_lists")


@pytest.fixture
def fake_popup():
    FakePopup.last = None

    with patch("food_lists_screen.Popup", FakePopup):
        yield FakePopup


def make_app(food_lists=None, current_list_id=None):
    return SimpleNamespace(
        food_lists=food_lists or [],
        current_list_id=current_list_id,
        current_list_name="",
        active_list_label=SimpleNamespace(text=""),
        root=SimpleNamespace(current="food_lists"),
        reload_food_lists=Mock(),
        select_food_list=Mock(),
        clear_active_food_list=Mock(),
        get_user_id=Mock(return_value="user-123"),
        get_access_token=Mock(return_value="test-token"),
        logout=Mock(),
    )


def find_widget(root, widget_type, **attributes):
    for widget in root.walk():
        if not isinstance(widget, widget_type):
            continue

        if all(getattr(widget, name) == value for name, value in attributes.items()):
            return widget

    raise AssertionError(
        f"Widget {widget_type.__name__} not found: {attributes}")


def popup_status(popup):
    return next(widget for widget in popup.content.walk() if isinstance(widget, Label))


def test_add_colored_background_tracks_widget_size_and_position():
    widget = BoxLayout()

    add_colored_background(widget)
    widget.size = (200, 100)
    widget.pos = (10, 20)


def test_on_pre_enter_reloads_and_renders_lists(screen):
    app = make_app()

    with (
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch.object(screen, "render_lists") as mock_render,
    ):
        screen.selected_list_id = 4
        screen.on_pre_enter()

    app.reload_food_lists.assert_called_once_with()
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


def test_create_popup_requires_name(screen, fake_popup):
    app = make_app()

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup.opened
    assert popup_status(popup).text == "Inserisci un nome per la lista"


def test_create_popup_rejects_duplicate_name(screen, fake_popup):
    app = make_app(food_lists=[{"id": 1, "name": " Cena "}])

    with patch("food_lists_screen.App.get_running_app", return_value=app):
        screen.open_create_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "cena"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    assert popup_status(popup).text == "Esiste già una lista con questo nome"


def test_create_popup_displays_request_error(screen, fake_popup):
    app = make_app()

    with (
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.create_food_list",
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch(
            "food_lists_screen.create_food_list",
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.rename_food_list",
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.rename_food_list") as mock_rename,
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.delete_food_list",
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.delete_food_list") as mock_delete,
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.delete_food_list"),
        patch.object(screen, "render_lists"),
    ):
        screen.open_delete_popup(None)
        popup = fake_popup.last
        find_widget(popup.content, RoundedButton,
                    text="Elimina").dispatch("on_release")

    assert app.food_lists == []
    app.clear_active_food_list.assert_called_once_with()


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
