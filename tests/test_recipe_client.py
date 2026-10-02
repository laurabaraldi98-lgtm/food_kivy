from unittest.mock import Mock, patch

import pytest
from requests import HTTPError, Timeout

from recipe_client import RECIPE_URL, generate_recipe
from supabase_client import get_authenticated_headers


RECIPE = {
    "title": "Pizza margherita",
    "servings": 2,
    "total_minutes": 180,
    "ingredients": [
        {"name": "Farina", "quantity": "300 g"},
    ],
    "steps": [
        "Prepara l'impasto.",
        "Lascia lievitare e cuoci.",
    ],
}


def test_generate_recipe_sends_authenticated_request():
    response = Mock()
    response.json.return_value = {"recipe": RECIPE}

    with patch("recipe_client.requests.post", return_value=response) as post:
        result = generate_recipe("Pizza", 2, "it", "test-token")

    post.assert_called_once_with(
        RECIPE_URL,
        headers=get_authenticated_headers("test-token"),
        json={
            "dish": "Pizza",
            "servings": 2,
            "language": "it",
        },
        timeout=(10, 60),
    )
    response.raise_for_status.assert_called_once_with()
    assert result == RECIPE


@pytest.mark.parametrize("status", [401, 429, 503])
def test_generate_recipe_propagates_http_errors(status):
    response = Mock()
    response.status_code = status
    error = HTTPError(response=response)
    response.raise_for_status.side_effect = error

    with patch("recipe_client.requests.post", return_value=response):
        with pytest.raises(HTTPError) as caught:
            generate_recipe("Pizza", 2, "en", "test-token")

    assert caught.value is error
    response.json.assert_not_called()


def test_generate_recipe_propagates_timeout():
    with patch("recipe_client.requests.post", side_effect=Timeout):
        with pytest.raises(Timeout):
            generate_recipe("Pizza", 2, "it", "test-token")


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "invalid",
        {},
        {"recipe": None},
        {"recipe": []},
    ],
)
def test_generate_recipe_rejects_invalid_response(payload):
    response = Mock()
    response.json.return_value = payload

    with patch("recipe_client.requests.post", return_value=response):
        with pytest.raises(ValueError, match="Invalid recipe response"):
            generate_recipe("Pizza", 2, "it", "test-token")


def test_generate_recipe_propagates_invalid_json():
    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    with patch("recipe_client.requests.post", return_value=response):
        with pytest.raises(ValueError, match="Invalid JSON"):
            generate_recipe("Pizza", 2, "it", "test-token")
