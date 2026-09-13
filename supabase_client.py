import requests

from config import SUPABASE_KEY, SUPABASE_URL


FOODS_URL = f"{SUPABASE_URL}/rest/v1/foods"
FOOD_LISTS_URL = f"{SUPABASE_URL}/rest/v1/food_lists"
GROUPS_URL = f"{SUPABASE_URL}/rest/v1/groups"
GROUP_MEMBERS_URL = f"{SUPABASE_URL}/rest/v1/group_members"
RPC_URL = f"{SUPABASE_URL}/rest/v1/rpc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}


def get_authenticated_headers(access_token):
    return {
        **HEADERS,
        "Authorization": f"Bearer {access_token}",
    }


def get_food_lists(access_token):
    response = requests.get(
        FOOD_LISTS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={
            "select": "id,name,is_default,owner_id,group_id",
            "order": "is_default.desc,created_at.asc",
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_foods(list_id, access_token):
    response = requests.get(
        FOODS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={
            "select": "name",
            "list_id": f"eq.{list_id}",
            "order": "name.asc",
        },
        timeout=10,
    )

    response.raise_for_status()

    return [
        item["name"]
        for item in response.json()
    ]


def create_food_list(name, owner_id, access_token):
    headers = {
        **get_authenticated_headers(access_token),
        "Prefer": "return=representation",
    }

    response = requests.post(
        FOOD_LISTS_URL,
        headers=headers,
        json={
            "name": name,
            "owner_id": owner_id,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()[0]


def rename_food_list(list_id, name, access_token):
    response = requests.patch(
        FOOD_LISTS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={"id": f"eq.{list_id}"},
        json={"name": name},
        timeout=10,
    )

    response.raise_for_status()


def delete_food_list(list_id, access_token):
    response = requests.delete(
        FOOD_LISTS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={"id": f"eq.{list_id}"},
        timeout=10,
    )

    response.raise_for_status()


def add_food(name, list_id, access_token):
    response = requests.post(
        FOODS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        json={
            "name": name,
            "list_id": list_id,
        },
        timeout=10,
    )

    response.raise_for_status()


def delete_food(name, list_id, access_token):
    response = requests.delete(
        FOODS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={
            "name": f"eq.{name}",
            "list_id": f"eq.{list_id}",
        },
        timeout=10,
    )

    response.raise_for_status()


def get_groups(access_token):
    response = requests.get(
        GROUPS_URL,
        headers=get_authenticated_headers(access_token),
        params={
            "select": "id,name,owner_id,created_at",
            "order": "created_at.asc",
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def create_group(name, owner_id, access_token):
    headers = {
        **get_authenticated_headers(access_token),
        "Prefer": "return=representation",
    }

    response = requests.post(
        GROUPS_URL,
        headers=headers,
        json={
            "name": name,
            "owner_id": owner_id,
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()[0]


def rename_group(group_id, name, access_token):
    response = requests.patch(
        GROUPS_URL,
        headers=get_authenticated_headers(access_token),
        params={"id": f"eq.{group_id}"},
        json={"name": name},
        timeout=10,
    )

    response.raise_for_status()


def delete_group(group_id, access_token):
    response = requests.delete(
        GROUPS_URL,
        headers=get_authenticated_headers(access_token),
        params={"id": f"eq.{group_id}"},
        timeout=10,
    )

    response.raise_for_status()


def get_group_members(group_id, access_token):
    response = requests.post(
        f"{RPC_URL}/get_group_members",
        headers=get_authenticated_headers(access_token),
        json={"target_group_id": group_id},
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def add_group_member(group_id, email, access_token):
    response = requests.post(
        f"{RPC_URL}/add_group_member_by_email",
        headers=get_authenticated_headers(access_token),
        json={
            "target_group_id": group_id,
            "member_email": email,
        },
        timeout=10,
    )

    response.raise_for_status()


def remove_group_member(group_id, user_id, access_token):
    response = requests.delete(
        GROUP_MEMBERS_URL,
        headers=get_authenticated_headers(access_token),
        params={
            "group_id": f"eq.{group_id}",
            "user_id": f"eq.{user_id}",
        },
        timeout=10,
    )

    response.raise_for_status()


def create_group_food_list(name, group_id, access_token):
    headers = {
        **get_authenticated_headers(access_token),
        "Prefer": "return=representation",
    }

    response = requests.post(
        FOOD_LISTS_URL,
        headers=headers,
        json={
            "name": name,
            "group_id": group_id,
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()[0]
