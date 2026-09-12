import requests

from config import SUPABASE_KEY, SUPABASE_URL


FOODS_URL = f"{SUPABASE_URL}/rest/v1/foods"
FOOD_LISTS_URL = f"{SUPABASE_URL}/rest/v1/food_lists"

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
            "select": "id,name,is_default",
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


def create_food_list(
    name,
    owner_id,
    access_token,
):
    response = requests.post(
        FOOD_LISTS_URL,
        headers={
            **get_authenticated_headers(
                access_token
            ),
            "Prefer": "return=representation",
        },
        json={
            "name": name,
            "owner_id": owner_id,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()[0]


def rename_food_list(
    list_id,
    name,
    access_token,
):
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


def delete_food_list(
    list_id,
    access_token,
):
    response = requests.delete(
        FOOD_LISTS_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={"id": f"eq.{list_id}"},
        timeout=10,
    )

    response.raise_for_status()


def add_food(
    name,
    list_id,
    access_token,
):
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


def delete_food(
    name,
    list_id,
    access_token,
):
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
