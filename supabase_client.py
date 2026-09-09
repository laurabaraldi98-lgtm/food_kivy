import requests

from config import SUPABASE_KEY, SUPABASE_URL


BASE_URL = f"{SUPABASE_URL}/rest/v1/foods"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}


def get_authenticated_headers(access_token):
    return {
        **HEADERS,
        "Authorization": f"Bearer {access_token}",
    }


def get_foods(access_token):
    response = requests.get(
        BASE_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={"select": "name"},
        timeout=10,
    )

    response.raise_for_status()

    return [
        item["name"]
        for item in response.json()
    ]


def add_food(name, access_token):
    response = requests.post(
        BASE_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        json={"name": name},
        timeout=10,
    )

    response.raise_for_status()


def delete_food(name, access_token):
    response = requests.delete(
        BASE_URL,
        headers=get_authenticated_headers(
            access_token
        ),
        params={"name": f"eq.{name}"},
        timeout=10,
    )

    response.raise_for_status()
