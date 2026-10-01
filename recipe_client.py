import requests

from config import SUPABASE_URL
from supabase_client import get_authenticated_headers


RECIPE_URL = f"{SUPABASE_URL.rstrip('/')}/functions/v1/generate-recipe"


def generate_recipe(dish, servings, language, access_token):
    """Request a recipe using the authenticated user's session."""
    response = requests.post(
        RECIPE_URL,
        headers=get_authenticated_headers(access_token),
        json={
            "dish": dish,
            "servings": servings,
            "language": language,
        },
        # Allow more time for AI generation than for ordinary database requests.
        timeout=(10, 60),
    )

    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Invalid recipe response")

    recipe = payload.get("recipe")

    if not isinstance(recipe, dict):
        raise ValueError("Invalid recipe response")

    return recipe
