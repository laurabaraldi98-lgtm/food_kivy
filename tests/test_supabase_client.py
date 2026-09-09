from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from supabase_client import (
    BASE_URL,
    HEADERS,
    add_food,
    delete_food,
    get_authenticated_headers,
    get_foods,
)


ACCESS_TOKEN = "test-access-token"

AUTHENTICATED_HEADERS = {
    **HEADERS,
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}


def test_get_authenticated_headers_adds_token():
    result = get_authenticated_headers(
        ACCESS_TOKEN
    )

    assert result == AUTHENTICATED_HEADERS
    assert "Authorization" not in HEADERS


@patch("supabase_client.requests.get")
def test_get_foods_sends_access_token(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = [
        {"name": "Pizza"},
        {"name": "Pasta"},
    ]
    mock_get.return_value = mock_response

    result = get_foods(ACCESS_TOKEN)

    mock_get.assert_called_once_with(
        BASE_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"select": "name"},
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == [
        "Pizza",
        "Pasta",
    ]


@patch("supabase_client.requests.post")
def test_add_food_sends_access_token(mock_post):
    mock_response = Mock()
    mock_post.return_value = mock_response

    add_food(
        "Pizza",
        ACCESS_TOKEN,
    )

    mock_post.assert_called_once_with(
        BASE_URL,
        headers=AUTHENTICATED_HEADERS,
        json={"name": "Pizza"},
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_delete_food_sends_access_token(mock_delete):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_food(
        "Pizza",
        ACCESS_TOKEN,
    )

    mock_delete.assert_called_once_with(
        BASE_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"name": "eq.Pizza"},
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.get")
def test_get_foods_raises_http_error(mock_get):
    mock_response = Mock()
    mock_response.status_code = 401

    http_error = HTTPError(
        "401 Client Error",
        response=mock_response,
    )

    mock_response.raise_for_status.side_effect = http_error
    mock_get.return_value = mock_response

    with pytest.raises(HTTPError) as error:
        get_foods(ACCESS_TOKEN)

    assert error.value.response.status_code == 401
