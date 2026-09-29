import pytest

from recipe_popup import RecipePopup


@pytest.mark.parametrize(
    ("language", "title", "servings", "generate", "cancel"),
    [
        ("it", "Genera ricetta", "Persone", "Genera", "Annulla"),
        ("en", "Generate recipe", "Servings", "Generate", "Cancel"),
    ],
)
def test_recipe_popup_uses_selected_language_and_preserves_dish(
    language, title, servings, generate, cancel
):
    popup = RecipePopup("Pasta al pomodoro", language)

    assert popup.title == title
    assert popup.dish == "Pasta al pomodoro"
    assert popup.dish_label.text == "Pasta al pomodoro"
    assert popup.servings_label.text == servings
    assert popup.generate_button.text == generate
    assert popup.cancel_button.text == cancel
    assert popup.generate_button.disabled

    popup.dish_label.size = (220, 60)
    assert popup.dish_label.text_size == [220, 60]


def test_recipe_popup_allows_selecting_number_of_people():
    popup = RecipePopup("Pizza", "it")

    assert popup.servings_spinner.text == "2"
    assert list(popup.servings_spinner.values) == [
        str(number) for number in range(1, 13)
    ]

    popup.servings_spinner.text = "4"

    assert popup.servings_spinner.text == "4"
