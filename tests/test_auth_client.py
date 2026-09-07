from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from auth_client import (
    AUTH_BASE_URL,
    HEADERS,
    sign_in,
    sign_up,
)


@patch("auth_client.requests.post")
def test_sign_up_sends_credentials(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "user": {
            "id": "user-123",
        }
    }
    mock_post.return_value = mock_response

    result = sign_up(
        "laura@example.com",
        "secure-password-123",
    )

    mock_post.assert_called_once_with(
        f"{AUTH_BASE_URL}/signup",
        headers=HEADERS,
        json={
            "email": "laura@example.com",
            "password": "secure-password-123",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == {
        "user": {
            "id": "user-123",
        }
    }


@patch("auth_client.requests.post")
def test_sign_in_sends_credentials(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
    }
    mock_post.return_value = mock_response

    result = sign_in(
        "laura@example.com",
        "secure-password-123",
    )

    mock_post.assert_called_once_with(
        f"{AUTH_BASE_URL}/token",
        headers=HEADERS,
        params={
            "grant_type": "password",
        },
        json={
            "email": "laura@example.com",
            "password": "secure-password-123",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
    }


@patch("auth_client.requests.post")
def test_sign_in_raises_http_error(mock_post):
    mock_response = Mock()
    mock_response.status_code = 400

    http_error = HTTPError(
        "400 Client Error",
        response=mock_response,
    )

    mock_response.raise_for_status.side_effect = http_error
    mock_post.return_value = mock_response

    with pytest.raises(HTTPError) as error:
        sign_in(
            "laura@example.com",
            "wrong-password",
        )

    assert error.value.response.status_code == 400
