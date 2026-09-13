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


def test_create_shared_list(screen, fake_popup):
    app = make_app()
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    created = {"id": 3, "name": "Famiglia", "group_id": 9}

    with (
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.create_group", return_value=group) as create_group,
        patch(
            "food_lists_screen.create_group_food_list", return_value=created
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.create_group", side_effect=RequestException),
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.create_group", return_value=group),
        patch("food_lists_screen.create_group_food_list",
              side_effect=RequestException),
        patch("food_lists_screen.delete_group", side_effect=cleanup_error) as cleanup,
    ):
        screen.open_create_popup(None, shared=True)
        popup = fake_popup.last
        find_widget(popup.content, TextInput).text = "Famiglia"
        find_widget(popup.content, RoundedButton,
                    text="Crea").dispatch("on_release")

    cleanup.assert_called_once_with(9, "test-token")
    assert popup_status(popup).text == "Impossibile creare la lista"


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


def test_rename_shared_list_updates_group(screen, fake_popup):
    selected = {"id": 1, "name": "Famiglia", "group_id": 9}
    group = {"id": 9, "name": "Famiglia", "owner_id": "user-123"}
    app = make_app(food_lists=[selected])
    screen.groups = [group]

    with (
        patch.object(screen, "get_selected_list", return_value=selected),
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.rename_food_list") as rename_list,
        patch("food_lists_screen.rename_group") as rename_group,
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.rename_food_list"),
        patch("food_lists_screen.rename_group", side_effect=RequestException),
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.delete_group") as delete,
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.delete_group", side_effect=RequestException),
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.remove_group_member",
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
        patch("food_lists_screen.App.get_running_app", return_value=app),
        patch("food_lists_screen.remove_group_member") as remove,
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
