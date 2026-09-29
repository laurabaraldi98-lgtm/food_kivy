from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner

from translations import translate
from ui_components import RoundedButton


class RecipePopup(Popup):
    def __init__(self, dish, language, **kwargs):
        self.dish = dish
        self.language = language

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
        )

        self.dish_label = Label(
            text=dish,
            font_size=sp(20),
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle",
            color=(0.02, 0.35, 0.28, 1),
        )
        self.dish_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        layout.add_widget(self.dish_label)

        servings_row = BoxLayout(
            spacing=dp(12),
            size_hint_y=None,
            height=dp(44),
        )

        self.servings_label = Label(
            text=translate(language, "servings"),
            font_size=sp(17),
            color=(0.02, 0.35, 0.28, 1),
        )

        self.servings_spinner = Spinner(
            text="2",
            values=tuple(str(number) for number in range(1, 13)),
            font_size=sp(17),
            size_hint_x=None,
            width=dp(90),
        )

        servings_row.add_widget(self.servings_label)
        servings_row.add_widget(self.servings_spinner)
        layout.add_widget(servings_row)

        actions = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(44),
        )

        self.cancel_button = RoundedButton(
            text=translate(language, "cancel"),
            font_size=sp(16),
            my_color=(0.40, 0.40, 0.40, 1),
            color=(1, 1, 1, 1),
        )

        # Enable generation when the recipe backend is connected.
        self.generate_button = RoundedButton(
            text=translate(language, "generate"),
            font_size=sp(16),
            disabled=True,
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        actions.add_widget(self.cancel_button)
        actions.add_widget(self.generate_button)
        layout.add_widget(actions)

        super().__init__(
            title=translate(language, "generate_recipe"),
            title_size=sp(19),
            content=layout,
            size_hint=(0.90, None),
            height=dp(280),
            background="",
            background_color=(0.70, 0.92, 0.88, 1),
            title_color=(0.02, 0.35, 0.28, 1),
            separator_color=(0.10, 0.55, 0.45, 1),
            **kwargs,
        )

        self.cancel_button.bind(on_release=self.dismiss)
