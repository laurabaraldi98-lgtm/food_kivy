from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.screenmanager import Screen, ScreenManager
from requests import RequestException

from auth_screen import AuthScreen


@pytest.fixture
def screen():
    return AuthScreen(name="auth")


def test_get_background_source_uses_tall_image_for_narrow_screen(
    screen,
):
    window = SimpleNamespace(width=300, height=800)

    with patch("auth_screen.Window", window):
        result = screen.get_background_source()

    assert result == "images/background_tall.png"


def test_get_background_source_uses_standard_image(screen):
    window = SimpleNamespace(width=600, height=800)

    with patch("auth_screen.Window", window):
        result = screen.get_background_source()

    assert result == "images/background.png"


def test_get_credentials_requires_email_and_password(screen):
    screen.email_input.text = ""
    screen.password_input.text = ""

    result = screen.get_credentials()

    assert result is None
    assert (
        screen.status_label.text
        == "Inserisci email e password"
    )


def test_get_credentials_normalizes_email(screen):
    screen.email_input.text = "  LAURA@EXAMPLE.COM  "
    screen.password_input.text = "secure-password"

    result = screen.get_credentials()

    assert result == (
        "laura@example.com",
        "secure-password",
    )


def test_handle_sign_in_stops_when_credentials_are_missing(
    screen,
):
    screen.email_input.text = ""
    screen.password_input.text = ""

    with patch("auth_screen.sign_in") as mock_sign_in:
        screen.handle_sign_in(None)

    mock_sign_in.assert_not_called()


def test_handle_sign_in_opens_food_screen(screen):
    screen.email_input.text = "laura@example.com"
    screen.password_input.text = "secure-password"

    session = {
        "access_token": "test-token",
    }

    app = SimpleNamespace(
        open_food_screen=Mock(),
    )

    with (
        patch(
            "auth_screen.sign_in",
            return_value=session,
        ) as mock_sign_in,
        patch(
            "auth_screen.App.get_running_app",
            return_value=app,
        ),
    ):
        screen.handle_sign_in(None)

    mock_sign_in.assert_called_once_with(
        "laura@example.com",
        "secure-password",
    )

    app.open_food_screen.assert_called_once_with(
        session,
    )

    assert screen.status_label.text == ""


def test_handle_sign_in_displays_error_when_request_fails(
    screen,
):
    screen.email_input.text = "laura@example.com"
    screen.password_input.text = "wrong-password"

    with patch(
        "auth_screen.sign_in",
        side_effect=RequestException,
    ):
        screen.handle_sign_in(None)

    assert (
        screen.status_label.text
        == "Email o password non corretti"
    )


def test_open_sign_up_changes_screen(screen):
    manager = ScreenManager()
    manager.add_widget(screen)
    manager.add_widget(
        Screen(name="signup"),
    )

    screen.status_label.text = "Old message"

    screen.open_sign_up(None)

    assert screen.status_label.text == ""
    assert manager.current == "signup"


def test_password_reset_requires_email(screen):
    screen.email_input.text = ""

    with patch(
        "auth_screen.request_password_reset",
    ) as mock_reset:
        screen.handle_password_reset(None)

    mock_reset.assert_not_called()

    assert (
        screen.status_label.text
        == "Inserisci prima la tua email"
    )


def test_password_reset_sends_normalized_email(screen):
    screen.email_input.text = "  LAURA@EXAMPLE.COM  "

    with patch(
        "auth_screen.request_password_reset",
    ) as mock_reset:
        screen.handle_password_reset(None)

    mock_reset.assert_called_once_with(
        "laura@example.com",
    )

    assert screen.status_label.text == (
        "Controlla la tua email per reimpostare la password"
    )


def test_password_reset_displays_error_when_request_fails(
    screen,
):
    screen.email_input.text = "laura@example.com"

    with patch(
        "auth_screen.request_password_reset",
        side_effect=RequestException,
    ):
        screen.handle_password_reset(None)

    assert screen.status_label.text == (
        "Impossibile inviare l'email di recupero"
    )
