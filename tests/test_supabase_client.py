from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from supabase_client import (
    FOOD_LISTS_URL,
    FOODS_URL,
    HEADERS,
    add_food,
    create_food_list,
    delete_food,
    delete_food_list,
    get_authenticated_headers,
    get_food_lists,
    get_foods,
    rename_food_list,
)


ACCESS_TOKEN = "test-access-token"
OWNER_ID = "11111111-1111-1111-1111-111111111111"
LIST_ID = 12

AUTHENTICATED_HEADERS = {
    **HEADERS,
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}

CREATION_HEADERS = {
    **AUTHENTICATED_HEADERS,
    "Prefer": "return=representation",
}


def test_get_authenticated_headers_adds_token():
    result = get_authenticated_headers(
        ACCESS_TOKEN
    )

    assert result == AUTHENTICATED_HEADERS
    assert "Authorization" not in HEADERS


@patch("supabase_client.requests.get")
def test_get_food_lists_sends_access_token(
    mock_get,
):
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "id": LIST_ID,
            "name": "I miei cibi",
            "is_default": True,
        }
    ]
    mock_get.return_value = mock_response

    result = get_food_lists(ACCESS_TOKEN)

    mock_get.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "select": "id,name,is_default",
            "order": "is_default.desc,created_at.asc",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == [
        {
            "id": LIST_ID,
            "name": "I miei cibi",
            "is_default": True,
        }
    ]


@patch("supabase_client.requests.get")
def test_get_foods_filters_by_list(
    mock_get,
):
    mock_response = Mock()
    mock_response.json.return_value = [
        {"name": "Pasta"},
        {"name": "Pizza"},
    ]
    mock_get.return_value = mock_response

    result = get_foods(
        LIST_ID,
        ACCESS_TOKEN,
    )

    mock_get.assert_called_once_with(
        FOODS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "select": "name",
            "list_id": f"eq.{LIST_ID}",
            "order": "name.asc",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == [
        "Pasta",
        "Pizza",
    ]


@patch("supabase_client.requests.post")
def test_create_food_list_returns_created_list(
    mock_post,
):
    created_list = {
        "id": LIST_ID,
        "name": "Lista weekend",
        "is_default": False,
    }

    mock_response = Mock()
    mock_response.json.return_value = [
        created_list
    ]
    mock_post.return_value = mock_response

    result = create_food_list(
        "Lista weekend",
        OWNER_ID,
        ACCESS_TOKEN,
    )

    mock_post.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=CREATION_HEADERS,
        json={
            "name": "Lista weekend",
            "owner_id": OWNER_ID,
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()

    assert result == created_list


@patch("supabase_client.requests.patch")
def test_rename_food_list_filters_by_id(
    mock_patch,
):
    mock_response = Mock()
    mock_patch.return_value = mock_response

    rename_food_list(
        LIST_ID,
        "Preferiti",
        ACCESS_TOKEN,
    )

    mock_patch.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{LIST_ID}"},
        json={"name": "Preferiti"},
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_delete_food_list_filters_by_id(
    mock_delete,
):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_food_list(
        LIST_ID,
        ACCESS_TOKEN,
    )

    mock_delete.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{LIST_ID}"},
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.post")
def test_add_food_includes_list_id(
    mock_post,
):
    mock_response = Mock()
    mock_post.return_value = mock_response

    add_food(
        "Pizza",
        LIST_ID,
        ACCESS_TOKEN,
    )

    mock_post.assert_called_once_with(
        FOODS_URL,
        headers=AUTHENTICATED_HEADERS,
        json={
            "name": "Pizza",
            "list_id": LIST_ID,
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_delete_food_filters_by_name_and_list(
    mock_delete,
):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_food(
        "Pizza",
        LIST_ID,
        ACCESS_TOKEN,
    )

    mock_delete.assert_called_once_with(
        FOODS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "name": "eq.Pizza",
            "list_id": f"eq.{LIST_ID}",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.get")
def test_get_foods_raises_http_error(
    mock_get,
):
    mock_response = Mock()
    mock_response.status_code = 401

    http_error = HTTPError(
        "401 Client Error",
        response=mock_response,
    )

    mock_response.raise_for_status.side_effect = (
        http_error
    )
    mock_get.return_value = mock_response

    with pytest.raises(HTTPError) as error:
        get_foods(
            LIST_ID,
            ACCESS_TOKEN,
        )

    assert error.value.response.status_code == 401
