import requests

from config import SUPABASE_KEY, SUPABASE_URL


AUTH_BASE_URL = f"{SUPABASE_URL}/auth/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}


def sign_up(email, password):
    response = requests.post(
        f"{AUTH_BASE_URL}/signup",
        headers=HEADERS,
        json={
            "email": email,
            "password": password,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def sign_in(email, password):
    response = requests.post(
        f"{AUTH_BASE_URL}/token",
        headers=HEADERS,
        params={"grant_type": "password"},
        json={
            "email": email,
            "password": password,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()
