import pytest

from ui_components import MenuButton, RoundedButton


def test_rounded_button_draws_and_updates_background():
    button = RoundedButton(
        my_color=(0.2, 0.3, 0.4, 1),
        pos=(10, 20),
        size=(120, 50),
    )

    assert button.background_normal == ""
    assert button.background_color == [0, 0, 0, 0]
    assert button.button_color.rgba == [0.2, 0.3, 0.4, 1]
    assert button.rounded_rect.pos == (10, 20)
    assert button.rounded_rect.size == (120, 50)

    button.pos = (30, 40)
    button.size = (150, 60)
    button.update_rounded_rect(button, button.size)

    assert button.rounded_rect.pos == (30, 40)
    assert button.rounded_rect.size == (150, 60)


def test_menu_button_draws_and_updates_hamburger_icon():
    button = MenuButton(pos=(10, 20), size=(100, 80))

    assert button.icon_color.rgba == [1, 1, 1, 1]
    assert button.top_line.points == pytest.approx([38, 72.8, 82, 72.8])
    assert button.middle_line.points == pytest.approx([38, 60, 82, 60])
    assert button.bottom_line.points == pytest.approx([38, 47.2, 82, 47.2])

    button.pos = (20, 30)
    button.size = (200, 100)
    button.update_rounded_rect(button, button.size)

    assert button.rounded_rect.pos == (20, 30)
    assert button.rounded_rect.size == (200, 100)
    assert button.top_line.points == pytest.approx([76, 96, 164, 96])
    assert button.middle_line.points == pytest.approx([76, 80, 164, 80])
    assert button.bottom_line.points == pytest.approx([76, 64, 164, 64])
