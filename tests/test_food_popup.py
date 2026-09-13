from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from requests import RequestException

from food_popup import show_food_popup
from ui_components import RoundedButton


class FakePopup:
    last = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.opened = False
        FakePopup.last = self

    def open(self):
        self.opened = True


class FakeScheduler:
    def __init__(self):
        self.calls = []

    def schedule_once(self, callback, delay):
        self.calls.append((callback, delay))

        if delay == 0.2:
            callback(0)

    def run_status_callback(self):
        callback = next(
            callback
            for callback, delay in self.calls
            if delay == 3
        )
        callback(0)


@pytest.fixture(autouse=True)
def fake_kivy_services():
    scheduler = FakeScheduler()
    clock = SimpleNamespace(
        schedule_once=scheduler.schedule_once
    )
    FakePopup.last = None

    with (
        patch("food_popup.Popup", FakePopup),
        patch("food_popup.Clock", clock),
    ):
        yield scheduler


def make_app(food=None):
    return SimpleNamespace(
        food=food or [],
        current_list_id=7,
        current_list_name="Cena",
        get_access_token=Mock(
            return_value="test-token"
        ),
    )


def find_widget(root, widget_type, **attributes):
    for widget in root.walk():
        if not isinstance(widget, widget_type):
            continue

        if all(
            getattr(widget, name) == value
            for name, value in attributes.items()
        ):
            return widget

    raise AssertionError(
        f"Widget {widget_type.__name__} not found: {attributes}"
    )


def open_popup(app):
    show_food_popup(app)
    return FakePopup.last


def get_controls(popup):
    return SimpleNamespace(
        list_label=find_widget(
            popup.content,
            Label,
            halign="left",
        ),
        status=find_widget(
            popup.content,
            Label,
            text="",
        ),
        food_input=find_widget(
            popup.content,
            TextInput,
            hint_text="Nome del cibo",
        ),
        add_button=find_widget(
            popup.content,
            RoundedButton,
            text="Aggiungi",
        ),
        delete_button=find_widget(
            popup.content,
            RoundedButton,
            text="Elimina",
        ),
    )


def test_popup_builds_empty_list_and_updates_layout(
    fake_kivy_services,
):
    app = make_app()
    popup = open_popup(app)

    assert popup.opened
    assert popup.title == "Cibi - Cena"
    assert find_widget(
        popup.content,
        Label,
        text="Lista vuota",
    )

    popup.content.size = (300, 400)
    popup.content.pos = (10, 20)

    scroll = find_widget(
        popup.content,
        ScrollView,
    )
    scroll.width += 1

    food_input = find_widget(
        popup.content,
        TextInput,
        hint_text="Nome del cibo",
    )
    with patch("food_popup.platform", "android"):
        food_input.focus = True
        food_input.focus = False

    assert any(
        delay == 0.2
        for _, delay in fake_kivy_services.calls
    )


def test_add_food_requires_a_name():
    popup = open_popup(make_app())
    controls = get_controls(popup)

    controls.add_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Scrivi un cibo da aggiungere"
    )


def test_add_food_rejects_duplicate(
    fake_kivy_services,
):
    popup = open_popup(
        make_app(["Pasta"])
    )
    controls = get_controls(popup)
    controls.food_input.text = "pasta"

    controls.add_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Pasta è già nella lista"
    )
    assert controls.food_input.text == ""

    fake_kivy_services.run_status_callback()

    assert controls.status.text == ""


def test_add_food_updates_remote_and_local_list():
    app = make_app(["Zuppa"])
    popup = open_popup(app)
    controls = get_controls(popup)
    controls.food_input.text = "pizza"

    with patch(
        "food_popup.add_food"
    ) as mock_add:
        controls.add_button.dispatch("on_press")

    mock_add.assert_called_once_with(
        "Pizza",
        7,
        "test-token",
    )
    assert app.food == ["Pizza", "Zuppa"]
    assert controls.list_label.text == "Pizza\nZuppa"
    assert controls.status.text == "Aggiunto: Pizza"
    assert controls.food_input.text == ""


def test_add_food_displays_request_error():
    popup = open_popup(make_app())
    controls = get_controls(popup)
    controls.food_input.text = "Pizza"

    with patch(
        "food_popup.add_food",
        side_effect=RequestException,
    ):
        controls.add_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Impossibile aggiungere il cibo"
    )


def test_delete_food_requires_a_name():
    popup = open_popup(
        make_app(["Pasta"])
    )
    controls = get_controls(popup)

    controls.delete_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Scrivi un cibo da eliminare"
    )


def test_delete_food_reports_missing_food(
    fake_kivy_services,
):
    popup = open_popup(
        make_app(["Pasta"])
    )
    controls = get_controls(popup)
    controls.food_input.text = "Pizza"

    controls.delete_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Pizza non è nella lista"
    )
    assert controls.food_input.text == ""

    fake_kivy_services.run_status_callback()

    assert controls.status.text == ""


def test_delete_food_updates_remote_and_local_list():
    app = make_app(["Pasta", "Pizza"])
    popup = open_popup(app)
    controls = get_controls(popup)
    controls.food_input.text = "pAsTa"

    with patch(
        "food_popup.delete_food"
    ) as mock_delete:
        controls.delete_button.dispatch("on_press")

    mock_delete.assert_called_once_with(
        "Pasta",
        7,
        "test-token",
    )
    assert app.food == ["Pizza"]
    assert controls.list_label.text == "Pizza"
    assert controls.status.text == "Eliminato: Pasta"
    assert controls.food_input.text == ""


def test_delete_food_displays_request_error():
    popup = open_popup(
        make_app(["Pasta"])
    )
    controls = get_controls(popup)
    controls.food_input.text = "Pasta"

    with patch(
        "food_popup.delete_food",
        side_effect=RequestException,
    ):
        controls.delete_button.dispatch("on_press")

    assert (
        controls.status.text
        == "Impossibile eliminare il cibo"
    )
