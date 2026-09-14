from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from requests import RequestException

from kivy.metrics import dp

from group_members_popup import add_colored_background, show_group_members_popup
from ui_components import RoundedButton


OWNER_GROUP = {
    "id": 9,
    "name": "Famiglia",
    "owner_id": "owner-1",
}
MEMBERS = [
    {
        "user_id": "owner-1",
        "email": "owner@example.com",
        "role": "owner",
    },
    {
        "user_id": "member-2",
        "email": "member@example.com",
        "role": "member",
    },
]


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


class FakeResponse:
    def __init__(self, message=None, invalid_json=False):
        self.message = message
        self.invalid_json = invalid_json

    def json(self):
        if self.invalid_json:
            raise ValueError
        return {"message": self.message or ""}


def make_error(message=None, invalid_json=False, without_response=False):
    error = RequestException()
    error.response = (
        None
        if without_response
        else FakeResponse(message=message, invalid_json=invalid_json)
    )
    return error


def make_app(user_id="owner-1"):
    return SimpleNamespace(
        get_user_id=Mock(return_value=user_id),
        get_access_token=Mock(return_value="test-token"),
    )


def find_widget(root, widget_type, **attributes):
    for widget in root.walk():
        if not isinstance(widget, widget_type):
            continue
        if all(
            getattr(widget, name, object()) == value
            for name, value in attributes.items()
        ):
            return widget
    raise AssertionError(
        f"Widget {widget_type.__name__} not found: {attributes}"
    )


def widget_texts(root, widget_type):
    return {
        widget.text
        for widget in root.walk()
        if isinstance(widget, widget_type)
    }


@pytest.fixture(autouse=True)
def reset_fake_popup():
    FakePopup.last = None


def test_add_colored_background_tracks_size_and_position():
    widget = BoxLayout()
    add_colored_background(widget)
    widget.size = (220, 120)
    widget.pos = (12, 24)


def test_owner_sees_members_and_management_controls():
    app = make_app()

    with (
        patch("group_members_popup.App.get_running_app", return_value=app),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=MEMBERS),
    ):
        show_group_members_popup(OWNER_GROUP)

    popup = FakePopup.last
    assert popup.opened
    assert popup.title == "Membri - Famiglia"
    assert popup.height == dp(430)
    assert find_widget(
        popup.content, TextInput, hint_text="Email del nuovo membro"
    )
    assert {"Aggiungi", "Rimuovi", "Chiudi"} <= widget_texts(
        popup.content, RoundedButton
    )
    assert "owner@example.com\nproprietario" in widget_texts(
        popup.content, Label
    )
    member_label = find_widget(
        popup.content,
        Label,
        text="member@example.com\nmembro",
    )
    member_label.size = (180, 44)
    assert member_label.text_size == [180, 44]


def test_regular_member_can_only_view_members():
    app = make_app(user_id="member-2")

    with (
        patch("group_members_popup.App.get_running_app", return_value=app),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=MEMBERS),
    ):
        show_group_members_popup(OWNER_GROUP)

    popup = FakePopup.last
    assert popup.height == dp(370)
    assert not any(
        isinstance(widget, TextInput) for widget in popup.content.walk()
    )
    assert widget_texts(popup.content, RoundedButton) == {"Chiudi"}


def test_initial_member_loading_error_is_displayed():
    app = make_app()

    with (
        patch("group_members_popup.App.get_running_app", return_value=app),
        patch("group_members_popup.Popup", FakePopup),
        patch(
            "group_members_popup.get_group_members",
            side_effect=RequestException,
        ),
    ):
        show_group_members_popup(OWNER_GROUP)

    assert "Impossibile caricare i membri" in widget_texts(
        FakePopup.last.content, Label
    )


def test_close_button_dismisses_popup():
    with (
        patch(
            "group_members_popup.App.get_running_app",
            return_value=make_app(),
        ),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=[]),
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(
            popup.content, RoundedButton, text="Chiudi"
        ).dispatch("on_release")

    assert popup.dismissed


def test_add_member_requires_email():
    with (
        patch(
            "group_members_popup.App.get_running_app",
            return_value=make_app(),
        ),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=[]),
        patch("group_members_popup.add_group_member") as add,
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(
            popup.content, RoundedButton, text="Aggiungi"
        ).dispatch("on_release")

    add.assert_not_called()
    assert "Inserisci un indirizzo email" in widget_texts(
        popup.content, Label
    )


def test_add_member_rejects_local_duplicate():
    with (
        patch(
            "group_members_popup.App.get_running_app",
            return_value=make_app(),
        ),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=MEMBERS),
        patch("group_members_popup.add_group_member") as add,
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(popup.content, TextInput).text = " MEMBER@EXAMPLE.COM "
        find_widget(
            popup.content, RoundedButton, text="Aggiungi"
        ).dispatch("on_release")

    add.assert_not_called()
    assert "Questo utente è già nella lista" in widget_texts(
        popup.content, Label
    )


def test_add_member_refreshes_list_and_clears_input():
    refreshed = MEMBERS + [
        {
            "user_id": "member-3",
            "email": "new@example.com",
            "role": "member",
        }
    ]
    app = make_app()

    with (
        patch("group_members_popup.App.get_running_app", return_value=app),
        patch("group_members_popup.Popup", FakePopup),
        patch(
            "group_members_popup.get_group_members",
            side_effect=[MEMBERS, refreshed],
        ) as get_members,
        patch("group_members_popup.add_group_member") as add,
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        email_input = find_widget(popup.content, TextInput)
        email_input.text = " New@Example.com "
        find_widget(
            popup.content, RoundedButton, text="Aggiungi"
        ).dispatch("on_release")

    add.assert_called_once_with(9, "new@example.com", "test-token")
    assert get_members.call_count == 2
    assert email_input.text == ""
    assert "new@example.com\nmembro" in widget_texts(popup.content, Label)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            make_error(without_response=True),
            "Impossibile aggiungere il membro",
        ),
        (
            make_error(invalid_json=True),
            "Impossibile aggiungere il membro",
        ),
        (
            make_error("User is already a member"),
            "Questo utente è già nella lista",
        ),
        (
            make_error("User not found"),
            "Nessun utente trovato con questa email",
        ),
        (
            make_error("Only the group owner can add members"),
            "Solo il proprietario può aggiungere membri",
        ),
        (
            make_error("Unexpected database error"),
            "Impossibile aggiungere il membro",
        ),
    ],
)
def test_add_member_translates_request_errors(error, expected):
    with (
        patch(
            "group_members_popup.App.get_running_app",
            return_value=make_app(),
        ),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=[]),
        patch("group_members_popup.add_group_member", side_effect=error),
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(popup.content, TextInput).text = "new@example.com"
        find_widget(
            popup.content, RoundedButton, text="Aggiungi"
        ).dispatch("on_release")

    assert expected in widget_texts(popup.content, Label)


def test_remove_member_refreshes_list():
    app = make_app()

    with (
        patch("group_members_popup.App.get_running_app", return_value=app),
        patch("group_members_popup.Popup", FakePopup),
        patch(
            "group_members_popup.get_group_members",
            side_effect=[MEMBERS, MEMBERS[:1]],
        ),
        patch("group_members_popup.remove_group_member") as remove,
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(
            popup.content, RoundedButton, text="Rimuovi"
        ).dispatch("on_release")

    remove.assert_called_once_with(9, "member-2", "test-token")
    assert "member@example.com\nmembro" not in widget_texts(
        popup.content, Label
    )


def test_remove_member_displays_request_error():
    with (
        patch(
            "group_members_popup.App.get_running_app",
            return_value=make_app(),
        ),
        patch("group_members_popup.Popup", FakePopup),
        patch("group_members_popup.get_group_members", return_value=MEMBERS),
        patch(
            "group_members_popup.remove_group_member",
            side_effect=make_error(without_response=True),
        ),
    ):
        show_group_members_popup(OWNER_GROUP)
        popup = FakePopup.last
        find_widget(
            popup.content, RoundedButton, text="Rimuovi"
        ).dispatch("on_release")

    assert "Impossibile rimuovere il membro" in widget_texts(
        popup.content, Label
    )
