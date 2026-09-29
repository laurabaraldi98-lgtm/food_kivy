from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from kivy.uix.label import Label

from food_lists_screen import FoodListsScreen


class FakePopup:
    last = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.opened = False
        self.dismissed = False
        FakePopup.last = self

    def open(self):
        self.opened = True

    def dismiss(self, *args):
        self.dismissed = True


@pytest.fixture
def screen():
    return FoodListsScreen(name="food_lists")


@pytest.fixture
def fake_popup():
    FakePopup.last = None

    with patch("food_list_popups.Popup", FakePopup):
        yield FakePopup


def make_app(food_lists=None, current_list_id=None):
    return SimpleNamespace(
        food_lists=food_lists or [],
        current_list_id=current_list_id,
        current_list_name="",
        active_list_label=SimpleNamespace(text=""),
        root=SimpleNamespace(current="food_lists"),
        reload_food_lists=Mock(),
        select_food_list=Mock(),
        clear_active_food_list=Mock(),
        get_user_id=Mock(return_value="user-123"),
        get_access_token=Mock(return_value="test-token"),
        logout=Mock(),
    )


def find_widget(root, widget_type, **attributes):
    for widget in root.walk():
        if not isinstance(widget, widget_type):
            continue

        if all(
            getattr(widget, name) == value
            for name, value in attributes.items()
        ):
            return widget

    raise AssertionError(
        f"Widget {widget_type.__name__} not found: {attributes}"
    )


def popup_status(popup):
    return next(
        widget
        for widget in popup.content.walk()
        if isinstance(widget, Label)
    )
