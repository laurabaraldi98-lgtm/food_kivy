from unittest.mock import Mock, patch

import pytest
from requests import HTTPError, RequestException, Response, Timeout

from recipe_popup import RecipePopup
from translations import translate


RECIPE = {
    "title": "Pasta al pomodoro",
    "servings": 2,
    "total_minutes": 25,
    "ingredients": [
        {"name": "Pasta", "quantity": "160 g"},
        {"name": "Pomodoro", "quantity": "200 g"},
    ],
    "steps": [
        "Cuoci la pasta.",
        "Aggiungi il pomodoro.",
    ],
}


def make_http_error(status):
    response = Response()
    response.status_code = status
    return HTTPError(response=response)


@pytest.fixture
def popup():
    return RecipePopup("Pasta al pomodoro", "it")


@pytest.mark.parametrize(
    ("language", "title", "servings", "generate", "close"),
    [
        ("it", "Genera ricetta", "Persone", "Genera", "Chiudi"),
        ("en", "Generate recipe", "Servings", "Generate", "Close"),
    ],
)
def test_recipe_popup_uses_selected_language_and_preserves_dish(
    language, title, servings, generate, close
):
    popup = RecipePopup("Pasta al pomodoro", language)

    assert popup.title == title
    assert popup.dish == "Pasta al pomodoro"
    assert popup.dish_label.text == "Pasta al pomodoro"
    assert popup.servings_label.text == servings
    assert popup.generate_button.text == generate
    assert popup.cancel_button.text == close
    assert not popup.generate_button.disabled
    assert not popup.is_generating
    assert not popup.has_recipe
    assert not popup._closed
    assert popup.controls.parent is popup.layout


def test_recipe_popup_wraps_text_and_adjusts_recipe_height(popup):
    popup.dish_label.size = (220, 60)
    popup.status_label.size = (220, 52)
    popup.recipe_label.width = 220
    popup.recipe_label.text = "A long recipe\n" * 20
    popup.recipe_label.texture_update()

    assert popup.dish_label.text_size == [220, 60]
    assert popup.status_label.text_size == [220, 52]
    assert popup.recipe_label.text_size == [220, None]
    assert popup.recipe_label.height == popup.recipe_label.texture_size[1]
    assert popup.recipe_label.height > 0
    assert not popup.recipe_label.markup
    assert not popup.recipe_scroll.do_scroll_x


def test_recipe_popup_allows_selecting_number_of_people(popup):
    assert popup.servings_spinner.text == "2"
    assert list(popup.servings_spinner.values) == [
        str(number) for number in range(1, 13)
    ]

    popup.servings_spinner.text = "4"

    assert popup.servings_spinner.text == "4"


def test_close_button_dismisses_popup(popup):
    with patch.object(popup, "dismiss") as dismiss:
        popup.cancel_button.dispatch("on_release")

    dismiss.assert_called_once()


def test_dismissing_popup_marks_it_closed(popup):
    popup.dispatch("on_dismiss")

    assert popup._closed


@pytest.mark.parametrize(
    ("error", "color"),
    [
        (False, (0.02, 0.35, 0.28, 1)),
        (True, (0.55, 0.20, 0.20, 1)),
    ],
)
def test_set_status_translates_message_and_sets_color(popup, error, color):
    popup.set_status("recipe_failed", error=error)

    assert popup.status_label.text == translate("it", "recipe_failed")
    assert tuple(popup.status_label.color) == color


def test_generate_button_starts_request_in_background(popup):
    app = Mock()
    app.get_access_token.return_value = "test-token"
    popup.servings_spinner.text = "4"
    popup.recipe_label.text = "Previous recipe"

    # Mock the worker so this test starts no real thread or network request.
    with (
        patch("recipe_popup.App.get_running_app", return_value=app),
        patch("recipe_popup.Thread") as thread,
    ):
        popup.generate_button.dispatch("on_release")

    app.get_access_token.assert_called_once_with()
    thread.assert_called_once_with(
        target=popup.request_recipe,
        args=(4, "test-token"),
        daemon=True,
    )
    thread.return_value.start.assert_called_once_with()

    assert popup.is_generating
    assert popup.generate_button.disabled
    assert popup.servings_spinner.disabled
    assert not popup.cancel_button.disabled
    assert popup.recipe_label.text == ""
    assert popup.status_label.text == translate("it", "recipe_loading")


@pytest.mark.parametrize("state", ["generating", "closed"])
def test_generate_ignores_duplicate_requests_and_closed_popup(popup, state):
    popup.is_generating = state == "generating"
    popup._closed = state == "closed"

    with (
        patch("recipe_popup.App.get_running_app") as get_app,
        patch("recipe_popup.Thread") as thread,
    ):
        popup.handle_generate(None)

    get_app.assert_not_called()
    thread.assert_not_called()


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (make_http_error(401), "recipe_auth_required"),
        (make_http_error(429), "recipe_rate_limited"),
        (RequestException("Connection failed"), "recipe_network_error"),
        (RuntimeError("Not authenticated"), "recipe_auth_required"),
    ],
)
def test_generate_handles_session_errors_without_starting_worker(
    popup, error, key
):
    app = Mock()
    app.get_access_token.side_effect = error

    with (
        patch("recipe_popup.App.get_running_app", return_value=app),
        patch("recipe_popup.Thread") as thread,
    ):
        popup.handle_generate(None)

    thread.assert_not_called()
    assert not popup.is_generating
    assert not popup.generate_button.disabled
    assert not popup.servings_spinner.disabled
    assert popup.controls.parent is popup.layout
    assert popup.status_label.text == translate("it", key)
    assert tuple(popup.status_label.color) == (0.55, 0.20, 0.20, 1)


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (make_http_error(400), "recipe_failed"),
        (make_http_error(401), "recipe_auth_required"),
        (make_http_error(403), "recipe_auth_required"),
        (make_http_error(429), "recipe_rate_limited"),
        (make_http_error(500), "recipe_failed"),
        (HTTPError("No response"), "recipe_failed"),
    ],
)
def test_http_errors_map_to_expected_messages(error, key):
    assert RecipePopup.get_http_error_key(error) == key


@pytest.mark.parametrize("language", ["it", "en"])
def test_format_recipe_includes_translated_sections_and_numbered_steps(language):
    popup = RecipePopup("Pasta al pomodoro", language)

    text = popup.format_recipe(RECIPE)

    assert text == "\n\n".join(
        [
            "Pasta al pomodoro",
            translate(language, "recipe_servings", servings=2),
            translate(language, "recipe_time", minutes=25),
            translate(language, "recipe_ingredients"),
            "- Pasta: 160 g\n- Pomodoro: 200 g",
            translate(language, "recipe_steps"),
            "1. Cuoci la pasta.\n\n2. Aggiungi il pomodoro.",
        ]
    )


def test_successful_request_schedules_result_on_ui_thread(popup):
    with (
        patch("recipe_popup.generate_recipe", return_value=RECIPE) as generate,
        patch("recipe_popup.Clock.schedule_once") as schedule,
        patch.object(popup, "finish_generation") as finish,
    ):
        popup.request_recipe(2, "test-token")

        generate.assert_called_once_with(
            "Pasta al pomodoro", 2, "it", "test-token"
        )
        schedule.assert_called_once()
        finish.assert_not_called()

        # Execute the queued UI callback without running Kivy's event loop.
        callback, delay = schedule.call_args.args
        assert delay == 0
        callback(0)

        finish.assert_called_once_with(popup.format_recipe(RECIPE), None)


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (make_http_error(401), "recipe_auth_required"),
        (make_http_error(429), "recipe_rate_limited"),
        (make_http_error(502), "recipe_failed"),
        (Timeout("Timed out"), "recipe_timeout"),
        (RequestException("Connection failed"), "recipe_network_error"),
        (ValueError("Invalid JSON"), "recipe_failed"),
    ],
)
def test_failed_request_schedules_error_on_ui_thread(popup, error, key):
    with (
        patch("recipe_popup.generate_recipe", side_effect=error),
        patch("recipe_popup.Clock.schedule_once") as schedule,
        patch.object(popup, "finish_generation") as finish,
    ):
        popup.request_recipe(2, "test-token")

        finish.assert_not_called()
        schedule.assert_called_once()
        callback, delay = schedule.call_args.args
        assert delay == 0
        callback(0)

        finish.assert_called_once_with("", key)


@pytest.mark.parametrize(
    "recipe",
    [
        {},
        {"ingredients": None},
        {
            **RECIPE,
            "ingredients": [{"name": "Pasta"}],
        },
    ],
)
def test_malformed_recipe_is_reported_as_failure(popup, recipe):
    with (
        patch("recipe_popup.generate_recipe", return_value=recipe),
        patch("recipe_popup.Clock.schedule_once") as schedule,
        patch.object(popup, "finish_generation") as finish,
    ):
        popup.request_recipe(2, "test-token")
        callback, _ = schedule.call_args.args
        callback(0)

        finish.assert_called_once_with("", "recipe_failed")


def test_finish_generation_displays_recipe_and_hides_options(popup):
    popup.is_generating = True
    popup.generate_button.disabled = True
    popup.servings_spinner.disabled = True
    popup.recipe_scroll.scroll_y = 0
    popup.set_status("recipe_failed", error=True)

    popup.finish_generation("Generated recipe", None)

    assert not popup.is_generating
    assert popup.has_recipe
    assert not popup.generate_button.disabled
    assert not popup.servings_spinner.disabled
    assert popup.recipe_label.text == "Generated recipe"
    assert popup.recipe_scroll.scroll_y == 1
    assert popup.controls.parent is None
    assert popup.controls not in popup.layout.children
    assert popup.title == translate("it", "recipe_generated")
    assert popup.generate_button.text == translate("it", "new_recipe")
    assert tuple(popup.status_label.color) == (0.02, 0.35, 0.28, 1)


def test_finish_generation_displays_error_and_restores_controls(popup):
    popup.is_generating = True
    popup.generate_button.disabled = True
    popup.servings_spinner.disabled = True

    popup.finish_generation("", "recipe_timeout")

    assert not popup.is_generating
    assert not popup.has_recipe
    assert not popup.generate_button.disabled
    assert not popup.servings_spinner.disabled
    assert popup.controls.parent is popup.layout
    assert popup.recipe_label.text == ""
    assert popup.status_label.text == translate("it", "recipe_timeout")
    assert tuple(popup.status_label.color) == (0.55, 0.20, 0.20, 1)


@pytest.mark.parametrize("error_key", [None, "recipe_timeout"])
def test_finish_generation_ignores_results_after_popup_is_closed(
    popup, error_key
):
    popup.is_generating = True
    popup.generate_button.disabled = True
    popup.servings_spinner.disabled = True
    popup.recipe_label.text = "Existing text"
    popup.status_label.text = "Existing status"
    popup.mark_closed(None)

    popup.finish_generation("Late recipe", error_key)

    assert not popup.is_generating
    assert not popup.has_recipe
    assert popup.recipe_label.text == "Existing text"
    assert popup.status_label.text == "Existing status"
    assert popup.generate_button.disabled
    assert popup.servings_spinner.disabled


@pytest.mark.parametrize("language", ["it", "en"])
def test_new_recipe_restores_options_without_sending_request(language):
    popup = RecipePopup("Pizza", language)
    popup.servings_spinner.text = "4"
    popup.finish_generation("Generated recipe", None)

    with (
        patch("recipe_popup.App.get_running_app") as get_app,
        patch("recipe_popup.Thread") as thread,
        patch("recipe_popup.generate_recipe") as generate,
    ):
        popup.generate_button.dispatch("on_release")

    get_app.assert_not_called()
    thread.assert_not_called()
    generate.assert_not_called()

    assert not popup.has_recipe
    assert not popup.is_generating
    assert popup.controls.parent is popup.layout
    assert popup.layout.children[-1] is popup.controls
    assert popup.recipe_label.text == ""
    assert popup.status_label.text == ""
    assert popup.servings_spinner.text == "4"
    assert popup.title == translate(language, "generate_recipe")
    assert popup.generate_button.text == translate(language, "generate")
    assert not popup.generate_button.disabled
    assert not popup.servings_spinner.disabled

    # Starting another recipe uses the newly selected number of servings.
    popup.servings_spinner.text = "3"
    app = Mock()
    app.get_access_token.return_value = "test-token"

    with (
        patch("recipe_popup.App.get_running_app", return_value=app),
        patch("recipe_popup.Thread") as thread,
    ):
        popup.generate_button.dispatch("on_release")

    thread.assert_called_once_with(
        target=popup.request_recipe,
        args=(3, "test-token"),
        daemon=True,
    )
    thread.return_value.start.assert_called_once_with()
    assert popup.is_generating
