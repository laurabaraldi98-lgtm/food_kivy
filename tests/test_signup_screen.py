from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.screenmanager import Screen, ScreenManager
from requests import RequestException

from signup_screen import SignUpScreen


@pytest.fixture
def screen():
    return SignUpScreen(name="signup")


def test_get_background_source_uses_tall_image_for_narrow_screen(
    screen,
):
    window = SimpleNamespace(width=300, height=800)

    with patch("signup_screen.Window", window):
        result = screen.get_background_source()

    assert result == "images/background_tall.png"


def test_get_background_source_uses_standard_image(screen):
    window = SimpleNamespace(width=600, height=800)

    with patch("signup_screen.Window", window):
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


def test_handle_sign_up_stops_when_credentials_are_missing(
    screen,
):
    screen.email_input.text = ""
    screen.password_input.text = ""

    with patch("signup_screen.sign_up") as mock_sign_up:
        screen.handle_sign_up(None)

    mock_sign_up.assert_not_called()


def test_handle_sign_up_rejects_short_password(screen):
    screen.email_input.text = "laura@example.com"
    screen.password_input.text = "12345"

    with patch("signup_screen.sign_up") as mock_sign_up:
        screen.handle_sign_up(None)

    mock_sign_up.assert_not_called()

    assert screen.status_label.text == (
        "La password deve avere almeno 6 caratteri"
    )


def test_handle_sign_up_opens_food_screen_when_session_is_returned(
    screen,
):
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
            "signup_screen.sign_up",
            return_value=session,
        ) as mock_sign_up,
        patch(
            "signup_screen.App.get_running_app",
            return_value=app,
        ),
    ):
        screen.handle_sign_up(None)

    mock_sign_up.assert_called_once_with(
        "laura@example.com",
        "secure-password",
    )

    app.open_food_screen.assert_called_once_with(
        session,
    )


def test_handle_sign_up_requests_email_confirmation(screen):
    screen.email_input.text = "laura@example.com"
    screen.password_input.text = "secure-password"

    with patch(
        "signup_screen.sign_up",
        return_value={
            "user": {
                "id": "user-123",
            },
        },
    ):
        screen.handle_sign_up(None)

    assert screen.status_label.color == [
        0.02,
        0.35,
        0.28,
        1,
    ]

    assert screen.status_label.text == (
        "Controlla la tua email per confermare l'account"
    )


def test_handle_sign_up_displays_error_when_request_fails(
    screen,
):
    screen.email_input.text = "laura@example.com"
    screen.password_input.text = "secure-password"

    with patch(
        "signup_screen.sign_up",
        side_effect=RequestException,
    ):
        screen.handle_sign_up(None)

    assert (
        screen.status_label.text
        == "Impossibile creare l'account"
    )


def test_open_sign_in_changes_screen(screen):
    manager = ScreenManager()
    manager.add_widget(
        Screen(name="auth"),
    )
    manager.add_widget(screen)
    manager.current = "signup"

    screen.status_label.text = "Old message"

    screen.open_sign_in(None)

    assert screen.status_label.text == ""
    assert manager.current == "auth"
