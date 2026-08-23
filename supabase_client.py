import requests

from config import SUPABASE_URL, SUPABASE_KEY


BASE_URL = f"{SUPABASE_URL}/rest/v1/foods"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}


def get_foods():
    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        params={"select": "name"},
        timeout=10,
    )

    response.raise_for_status()

    return [item["name"] for item in response.json()]


def add_food(name):
    response = requests.post(
        BASE_URL,
        headers=HEADERS,
        json={"name": name},
        timeout=10,
    )

    response.raise_for_status()


def delete_food(name):
    response = requests.delete(
        BASE_URL,
        headers=HEADERS,
        params={"name": f"eq.{name}"},
        timeout=10,
    )

    response.raise_for_status()
