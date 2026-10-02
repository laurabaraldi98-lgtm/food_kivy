from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from requests import HTTPError, RequestException, Timeout

from recipe_client import generate_recipe
from translations import translate
from ui_components import RoundedButton


class RecipePopup(Popup):
    def __init__(self, dish, language, **kwargs):
        self.dish = dish
        self.language = language
        self.is_generating = False
        self.has_recipe = False
        self._closed = False

        self.layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
        )

        self.controls = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(156),
        )

        self.dish_label = Label(
            text=dish,
            font_size=sp(20),
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle",
            color=(0.02, 0.35, 0.28, 1),
        )
        self.dish_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.controls.add_widget(self.dish_label)

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
        self.controls.add_widget(servings_row)

        self.status_label = Label(
            text="",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(52),
            halign="center",
            valign="middle",
            color=(0.02, 0.35, 0.28, 1),
        )
        self.status_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.controls.add_widget(self.status_label)
        self.layout.add_widget(self.controls)

        self.recipe_scroll = ScrollView(do_scroll_x=False)

        # Wrap long recipes and let the ScrollView handle their full height.
        self.recipe_label = Label(
            text="",
            font_size=sp(16),
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(0.02, 0.35, 0.28, 1),
            markup=False,
        )
        self.recipe_label.bind(
            width=lambda instance, value: setattr(
                instance, "text_size", (value, None)
            ),
            texture_size=lambda instance, value: setattr(
                instance, "height", value[1]
            ),
        )

        self.recipe_scroll.add_widget(self.recipe_label)
        self.layout.add_widget(self.recipe_scroll)

        actions = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(44),
        )

        self.cancel_button = RoundedButton(
            text=translate(language, "close"),
            font_size=sp(16),
            my_color=(0.40, 0.40, 0.40, 1),
            color=(1, 1, 1, 1),
        )

        self.generate_button = RoundedButton(
            text=translate(language, "generate"),
            font_size=sp(16),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        actions.add_widget(self.cancel_button)
        actions.add_widget(self.generate_button)
        self.layout.add_widget(actions)

        super().__init__(
            title=translate(language, "generate_recipe"),
            title_size=sp(19),
            content=self.layout,
            size_hint=(0.92, 0.90),
            background="",
            background_color=(0.70, 0.92, 0.88, 1),
            title_color=(0.02, 0.35, 0.28, 1),
            separator_color=(0.10, 0.55, 0.45, 1),
            **kwargs,
        )

        self.cancel_button.bind(on_release=self.dismiss)
        self.generate_button.bind(on_release=self.handle_generate)
        self.bind(on_dismiss=self.mark_closed)

    def mark_closed(self, instance):
        # Ignore a response that arrives after the user closes this popup.
        self._closed = True

    def set_status(self, key, error=False):
        self.status_label.text = translate(self.language, key)
        self.status_label.color = (
            (0.55, 0.20, 0.20, 1)
            if error
            else (0.02, 0.35, 0.28, 1)
        )

    def show_recipe(self, text):
        self.has_recipe = True
        self.recipe_label.text = text
        self.recipe_scroll.scroll_y = 1

        # Remove the controls so the recipe receives their space.
        self.layout.remove_widget(self.controls)
        self.title = translate(self.language, "recipe_generated")
        self.generate_button.text = translate(self.language, "new_recipe")

    def show_recipe_options(self):
        self.has_recipe = False
        self.recipe_label.text = ""
        self.status_label.text = ""
        self.recipe_scroll.scroll_y = 1
        self.title = translate(self.language, "generate_recipe")
        self.generate_button.text = translate(self.language, "generate")

        # Kivy stores children in reverse order; index 2 places controls at the top.
        self.layout.add_widget(self.controls, index=2)

    def handle_generate(self, instance):
        if self.is_generating or self._closed:
            return

        if self.has_recipe:
            self.show_recipe_options()
            return

        # Session renewal may update the app, so obtain the token on the UI thread.
        try:
            app = App.get_running_app()
            access_token = app.get_access_token()
        except HTTPError as error:
            self.set_status(self.get_http_error_key(error), error=True)
            return
        except RequestException:
            self.set_status("recipe_network_error", error=True)
            return
        except RuntimeError:
            self.set_status("recipe_auth_required", error=True)
            return

        servings = int(self.servings_spinner.text)

        self.is_generating = True
        self.generate_button.disabled = True
        self.servings_spinner.disabled = True
        self.recipe_label.text = ""
        self.set_status("recipe_loading")

        # Keep the Gemini request off the UI thread.
        Thread(
            target=self.request_recipe,
            args=(servings, access_token),
            daemon=True,
        ).start()

    @staticmethod
    def get_http_error_key(error):
        response = error.response

        if response is not None:
            if response.status_code in (401, 403):
                return "recipe_auth_required"
            if response.status_code == 429:
                return "recipe_rate_limited"

        return "recipe_failed"

    def request_recipe(self, servings, access_token):
        text = ""
        error_key = None

        try:
            recipe = generate_recipe(
                self.dish,
                servings,
                self.language,
                access_token,
            )
            text = self.format_recipe(recipe)
        except HTTPError as error:
            error_key = self.get_http_error_key(error)
        except Timeout:
            error_key = "recipe_timeout"
        except RequestException:
            error_key = "recipe_network_error"
        except (ValueError, KeyError, TypeError):
            error_key = "recipe_failed"

        # Widget changes must run on Kivy's UI thread.
        Clock.schedule_once(
            lambda dt: self.finish_generation(text, error_key),
            0,
        )

    def format_recipe(self, recipe):
        ingredients = "\n".join(
            f"- {item['name']}: {item['quantity']}"
            for item in recipe["ingredients"]
        )
        steps = "\n\n".join(
            f"{number}. {step}"
            for number, step in enumerate(recipe["steps"], start=1)
        )

        return "\n\n".join(
            [
                recipe["title"],
                translate(
                    self.language,
                    "recipe_servings",
                    servings=recipe["servings"],
                ),
                translate(
                    self.language,
                    "recipe_time",
                    minutes=recipe["total_minutes"],
                ),
                translate(self.language, "recipe_ingredients"),
                ingredients,
                translate(self.language, "recipe_steps"),
                steps,
            ]
        )

    def finish_generation(self, text, error_key):
        self.is_generating = False

        if self._closed:
            return

        self.generate_button.disabled = False
        self.servings_spinner.disabled = False

        if error_key is not None:
            self.set_status(error_key, error=True)
            return

        self.set_status("recipe_generated")
        self.show_recipe(text)
