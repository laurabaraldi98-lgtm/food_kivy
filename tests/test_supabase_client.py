from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from supabase_client import (
    FOOD_LISTS_URL,
    FOODS_URL,
    GROUP_MEMBERS_URL,
    GROUPS_URL,
    HEADERS,
    RPC_URL,
    add_food,
    add_group_member,
    create_food_list,
    create_group,
    create_group_food_list,
    delete_food,
    delete_food_list,
    delete_group,
    get_authenticated_headers,
    get_food_lists,
    get_foods,
    get_group_members,
    get_groups,
    remove_group_member,
    rename_food_list,
    rename_group,
)


ACCESS_TOKEN = "test-access-token"
OWNER_ID = "11111111-1111-1111-1111-111111111111"
MEMBER_ID = "22222222-2222-2222-2222-222222222222"
MEMBER_EMAIL = "member@example.com"
LIST_ID = 12
GROUP_ID = 7

AUTHENTICATED_HEADERS = {
    **HEADERS,
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}

CREATION_HEADERS = {
    **AUTHENTICATED_HEADERS,
    "Prefer": "return=representation",
}


def test_get_authenticated_headers_adds_token():
    result = get_authenticated_headers(ACCESS_TOKEN)

    assert result == AUTHENTICATED_HEADERS
    assert "Authorization" not in HEADERS


@patch("supabase_client.requests.get")
def test_get_food_lists_sends_access_token(mock_get):
    food_lists = [{
        "id": LIST_ID,
        "name": "I miei cibi",
        "is_default": True,
        "owner_id": OWNER_ID,
        "group_id": None,
    }]

    mock_response = Mock()
    mock_response.json.return_value = food_lists
    mock_get.return_value = mock_response

    result = get_food_lists(ACCESS_TOKEN)

    mock_get.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "select": "id,name,is_default,owner_id,group_id",
            "order": "is_default.desc,created_at.asc",
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert result == food_lists


@patch("supabase_client.requests.get")
def test_get_foods_filters_by_list(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = [
        {"name": "Pasta"},
        {"name": "Pizza"},
    ]
    mock_get.return_value = mock_response

    result = get_foods(LIST_ID, ACCESS_TOKEN)

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
    assert result == ["Pasta", "Pizza"]


@patch("supabase_client.requests.post")
def test_create_food_list_returns_created_list(mock_post):
    created_list = {
        "id": LIST_ID,
        "name": "Lista weekend",
        "is_default": False,
    }

    mock_response = Mock()
    mock_response.json.return_value = [created_list]
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
def test_rename_food_list_filters_by_id(mock_patch):
    mock_response = Mock()
    mock_patch.return_value = mock_response

    rename_food_list(LIST_ID, "Preferiti", ACCESS_TOKEN)

    mock_patch.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{LIST_ID}"},
        json={"name": "Preferiti"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_delete_food_list_filters_by_id(mock_delete):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_food_list(LIST_ID, ACCESS_TOKEN)

    mock_delete.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{LIST_ID}"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.post")
def test_add_food_includes_list_id(mock_post):
    mock_response = Mock()
    mock_post.return_value = mock_response

    add_food("Pizza", LIST_ID, ACCESS_TOKEN)

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
def test_delete_food_filters_by_name_and_list(mock_delete):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_food("Pizza", LIST_ID, ACCESS_TOKEN)

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
        get_foods(LIST_ID, ACCESS_TOKEN)

    assert error.value.response.status_code == 401


@patch("supabase_client.requests.get")
def test_get_groups_returns_accessible_groups(mock_get):
    groups = [{
        "id": GROUP_ID,
        "name": "Famiglia",
        "owner_id": OWNER_ID,
        "created_at": "2026-09-13T13:00:00+00:00",
    }]

    mock_response = Mock()
    mock_response.json.return_value = groups
    mock_get.return_value = mock_response

    result = get_groups(ACCESS_TOKEN)

    mock_get.assert_called_once_with(
        GROUPS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "select": "id,name,owner_id,created_at",
            "order": "created_at.asc",
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert result == groups


@patch("supabase_client.requests.post")
def test_create_group_returns_created_group(mock_post):
    created_group = {
        "id": GROUP_ID,
        "name": "Famiglia",
        "owner_id": OWNER_ID,
    }

    mock_response = Mock()
    mock_response.json.return_value = [created_group]
    mock_post.return_value = mock_response

    result = create_group("Famiglia", OWNER_ID, ACCESS_TOKEN)

    mock_post.assert_called_once_with(
        GROUPS_URL,
        headers=CREATION_HEADERS,
        json={
            "name": "Famiglia",
            "owner_id": OWNER_ID,
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert result == created_group


@patch("supabase_client.requests.patch")
def test_rename_group_filters_by_id(mock_patch):
    mock_response = Mock()
    mock_patch.return_value = mock_response

    rename_group(GROUP_ID, "Casa", ACCESS_TOKEN)

    mock_patch.assert_called_once_with(
        GROUPS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{GROUP_ID}"},
        json={"name": "Casa"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_delete_group_filters_by_id(mock_delete):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    delete_group(GROUP_ID, ACCESS_TOKEN)

    mock_delete.assert_called_once_with(
        GROUPS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={"id": f"eq.{GROUP_ID}"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.post")
def test_get_group_members_returns_members(mock_post):
    members = [{
        "user_id": MEMBER_ID,
        "email": MEMBER_EMAIL,
        "role": "member",
    }]

    mock_response = Mock()
    mock_response.json.return_value = members
    mock_post.return_value = mock_response

    result = get_group_members(GROUP_ID, ACCESS_TOKEN)

    mock_post.assert_called_once_with(
        f"{RPC_URL}/get_group_members",
        headers=AUTHENTICATED_HEADERS,
        json={"target_group_id": GROUP_ID},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert result == members


@patch("supabase_client.requests.post")
def test_add_group_member_sends_email(mock_post):
    mock_response = Mock()
    mock_post.return_value = mock_response

    add_group_member(GROUP_ID, MEMBER_EMAIL, ACCESS_TOKEN)

    mock_post.assert_called_once_with(
        f"{RPC_URL}/add_group_member_by_email",
        headers=AUTHENTICATED_HEADERS,
        json={
            "target_group_id": GROUP_ID,
            "member_email": MEMBER_EMAIL,
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.delete")
def test_remove_group_member_filters_membership(mock_delete):
    mock_response = Mock()
    mock_delete.return_value = mock_response

    remove_group_member(
        GROUP_ID,
        MEMBER_ID,
        ACCESS_TOKEN,
    )

    mock_delete.assert_called_once_with(
        GROUP_MEMBERS_URL,
        headers=AUTHENTICATED_HEADERS,
        params={
            "group_id": f"eq.{GROUP_ID}",
            "user_id": f"eq.{MEMBER_ID}",
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()


@patch("supabase_client.requests.post")
def test_create_group_food_list_returns_created_list(mock_post):
    created_list = {
        "id": LIST_ID,
        "name": "Cene insieme",
        "group_id": GROUP_ID,
    }

    mock_response = Mock()
    mock_response.json.return_value = [created_list]
    mock_post.return_value = mock_response

    result = create_group_food_list(
        "Cene insieme",
        GROUP_ID,
        ACCESS_TOKEN,
    )

    mock_post.assert_called_once_with(
        FOOD_LISTS_URL,
        headers=CREATION_HEADERS,
        json={
            "name": "Cene insieme",
            "group_id": GROUP_ID,
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert result == created_list
