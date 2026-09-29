import random
import time

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from requests import HTTPError, RequestException

from auth_client import refresh_session, sign_out
from auth_screen import AuthScreen
from food_lists_screen import FoodListsScreen
from language_settings import load_language, save_language
from recipe_popup import RecipePopup
from session_storage import (
    clear_refresh_token,
    load_refresh_token,
    save_refresh_token,
)
from signup_screen import SignUpScreen
from supabase_client import get_food_lists, get_foods
from translations import translate
from ui_components import MenuButton, RoundedButton


if platform not in ("android", "ios"):
    Window.size = (360, 640)

if platform == "android":  # pragma: no cover
    Window.softinput_mode = "below_target"

Window.clearcolor = (0.70, 0.92, 0.88, 1)
Window.set_icon("images/icon.png")


class FoodApp(App):
    language = "it"

    def build(self):
        self.session = None
        self.token_refresh_at = None
        self.food = []
        self.food_lists = []
        self.current_list_id = None
        self.current_list_name = ""
        self.selected_food = None
        self.result_message_key = None
        self.language = load_language(self.user_data_dir)

        home_screen = Screen(name="food")
        home_screen.add_widget(self.build_home())

        manager = ScreenManager()

        # Apply the saved language when the account screens are created.
        auth_screen = AuthScreen(name="auth")
        auth_screen.refresh_texts(self.language)
        manager.add_widget(auth_screen)

        signup_screen = SignUpScreen(name="signup")
        signup_screen.refresh_texts(self.language)
        manager.add_widget(signup_screen)

        manager.add_widget(home_screen)

        lists_screen = FoodListsScreen(name="food_lists")
        lists_screen.refresh_texts(self.language)
        manager.add_widget(lists_screen)

        manager.current = "auth"
        return manager

    def on_start(self):
        # Restore the session saved during the previous login.
        token = load_refresh_token(self.user_data_dir)
        if not token:
            return

        try:
            session = refresh_session(token)
        except HTTPError as error:
            if (
                error.response is not None
                and error.response.status_code in (400, 401)
            ):
                clear_refresh_token(self.user_data_dir)
            return
        except RequestException:
            # Keep the saved token if the network is temporarily unavailable.
            return

        self.open_food_screen(session)

    def build_home(self):
        root = FloatLayout()

        ratio = Window.width / Window.height
        background_source = (
            "images/background_tall.png"
            if ratio < 0.48
            else "images/background.png"
        )

        background = Image(
            source=background_source,
            fit_mode="cover",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        root.add_widget(background)

        self.title_label = Label(
            text=translate(self.language, "home_title"),
            font_name="fonts/Pacifico-Regular.ttf",
            font_size=sp(34),
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.79},
            color=(0.02, 0.35, 0.28, 1),
        )

        self.choose_button = RoundedButton(
            text=translate(self.language, "choose_for_me"),
            font_size=sp(18),
            size_hint=(0.68, None),
            height=dp(48),
            pos_hint={"center_x": 0.5, "center_y": 0.62},
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.result = Label(
            text="",
            font_name="fonts/Pacifico-Regular.ttf",
            font_size=sp(30),
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.48},
            color=(0.02, 0.35, 0.28, 1),
        )

        self.recipe_button = RoundedButton(
            text=translate(self.language, "generate_recipe"),
            font_size=sp(16),
            size_hint=(0.60, None),
            height=dp(44),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            opacity=0,
            disabled=True,
            my_color=(0.25, 0.55, 0.70, 1),
            color=(1, 1, 1, 1),
        )
        self.recipe_button.bind(on_release=self.open_recipe_popup)

        self.active_list_label = Label(
            text=translate(self.language, "no_active_list"),
            font_size=sp(16),
            size_hint=(0.9, 0.08),
            pos_hint={"center_x": 0.5, "center_y": 0.20},
            color=(0.02, 0.35, 0.28, 1),
        )

        self.menu_button = MenuButton(
            text="",
            size_hint=(None, None),
            width=dp(48),
            height=dp(48),
            pos_hint={"x": 0.03, "top": 0.97},
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.menu = DropDown(auto_width=False, width=dp(170))

        self.lists_button = RoundedButton(
            text=translate(self.language, "manage_lists"),
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        self.lists_button.bind(on_release=self.open_food_lists_from_menu)

        self.language_button = RoundedButton(
            text="Italiano" if self.language == "en" else "English",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.language_flag = Image(
            source=(
                "images/flag_it.png"
                if self.language == "en"
                else "images/flag_en.png"
            ),
            fit_mode="contain",
            size_hint=(None, None),
            size=(dp(34), dp(34)),
        )
        self.language_button.add_widget(self.language_flag)

        def position_language_flag(*args):
            self.language_flag.pos = (
                self.language_button.x + dp(12),
                self.language_button.center_y - self.language_flag.height / 2,
            )

        self.language_button.bind(
            pos=position_language_flag,
            size=position_language_flag,
        )
        position_language_flag()
        self.language_button.bind(on_release=self.toggle_language)

        self.logout_button = RoundedButton(
            text=translate(self.language, "logout"),
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.55, 0.20, 0.20, 1),
            color=(1, 1, 1, 1),
        )
        self.logout_button.bind(on_release=self.logout_from_menu)

        self.menu.add_widget(self.lists_button)
        self.menu.add_widget(self.language_button)
        self.menu.add_widget(self.logout_button)

        self.menu_button.bind(on_release=self.menu.open)
        self.choose_button.bind(on_press=self.choose_food)

        root.add_widget(self.title_label)
        root.add_widget(self.choose_button)
        root.add_widget(self.result)
        root.add_widget(self.recipe_button)
        root.add_widget(self.active_list_label)
        root.add_widget(self.menu_button)

        return root

    def set_session(self, session):
        self.session = session

        expires_in = session.get("expires_in")
        if isinstance(expires_in, (int, float)):
            # Refresh 60 seconds early, or after 90% for short sessions.
            seconds_until_refresh = max(
                expires_in - 60,
                expires_in * 0.9,
            )
            self.token_refresh_at = (
                time.monotonic() + seconds_until_refresh
            )
        else:
            self.token_refresh_at = None

        # Replace the stored refresh token after every successful renewal.
        refresh_token = session.get("refresh_token")
        if refresh_token:
            save_refresh_token(self.user_data_dir, refresh_token)

    def open_food_screen(self, session):
        self.set_session(session)
        self.reload_food_lists()
        self.root.current = "food"

    def reload_food_lists(self):
        previous_list_id = self.current_list_id
        self.food_lists = get_food_lists(self.get_access_token())

        selected_list = next(
            (
                food_list
                for food_list in self.food_lists
                if food_list["id"] == previous_list_id
            ),
            self.food_lists[0] if self.food_lists else None,
        )

        if selected_list:
            self.select_food_list(selected_list)
        else:
            self.clear_active_food_list()

    def get_access_token(self):
        if not self.session:
            raise RuntimeError("User is not authenticated")

        refresh_at = getattr(self, "token_refresh_at", None)

        if refresh_at is not None and time.monotonic() >= refresh_at:
            # Renew before sending a request with an expired access token.
            refresh_token = self.session.get("refresh_token")
            try:
                new_session = refresh_session(refresh_token)
            except HTTPError as error:
                if (
                    error.response is not None
                    and error.response.status_code in (400, 401)
                ):
                    # A rejected refresh token cannot restore this session.
                    clear_refresh_token(self.user_data_dir)
                    self.session = None
                    self.token_refresh_at = None
                    self.food_lists = []
                    self.clear_active_food_list()
                    self.root.current = "auth"
                raise

            self.set_session(new_session)

        return self.session["access_token"]

    def get_user_id(self):
        if not self.session:
            raise RuntimeError("User is not authenticated")

        return self.session["user"]["id"]

    def set_selected_food(self, food):
        # Keep the recipe button consistent with the selected dish.
        self.selected_food = food
        has_selection = food is not None
        self.recipe_button.disabled = not has_selection
        self.recipe_button.opacity = 1 if has_selection else 0

    def select_food_list(self, food_list):
        self.current_list_id = food_list["id"]
        self.current_list_name = food_list["name"]
        self.food = get_foods(
            self.current_list_id,
            self.get_access_token(),
        )

        self.active_list_label.text = translate(
            self.language,
            "active_list",
            name=self.current_list_name,
        )
        self.set_selected_food(None)
        self.result_message_key = None
        self.result.text = ""

    def clear_active_food_list(self):
        self.current_list_id = None
        self.current_list_name = ""
        self.food = []
        self.active_list_label.text = translate(
            self.language, "no_active_list"
        )
        self.set_selected_food(None)
        self.result_message_key = None
        self.result.text = ""

    def open_recipe_popup(self, instance):
        if self.selected_food is None:
            return

        RecipePopup(self.selected_food, self.language).open()

    def open_food_lists_from_menu(self, instance):
        self.menu.dismiss()
        self.root.current = "food_lists"

    def toggle_language(self, instance):
        self.menu.dismiss()
        next_language = "en" if self.language == "it" else "it"
        self.set_language(next_language)

    def set_language(self, language):
        if language not in ("it", "en"):
            raise ValueError(f"Unsupported language: {language}")

        save_language(self.user_data_dir, language)
        self.language = language
        self.refresh_home_texts()

        # Update the account screens when the user changes language.
        self.root.get_screen("auth").refresh_texts(language)
        self.root.get_screen("signup").refresh_texts(language)
        self.root.get_screen("food_lists").refresh_texts(language)
        if self.root.current == "food_lists":
            self.root.get_screen("food_lists").render_lists()

    def refresh_home_texts(self):
        self.title_label.text = translate(self.language, "home_title")
        self.choose_button.text = translate(
            self.language, "choose_for_me"
        )
        self.recipe_button.text = translate(self.language, "generate_recipe")
        self.lists_button.text = translate(
            self.language, "manage_lists"
        )
        self.logout_button.text = translate(self.language, "logout")
        self.language_button.text = (
            "Italiano" if self.language == "en" else "English"
        )
        self.language_flag.source = (
            "images/flag_it.png"
            if self.language == "en"
            else "images/flag_en.png"
        )

        if self.current_list_id is None:
            self.active_list_label.text = translate(
                self.language, "no_active_list"
            )
        else:
            self.active_list_label.text = translate(
                self.language,
                "active_list",
                name=self.current_list_name,
            )

        if getattr(self, "result_message_key", None):
            message = translate(self.language, self.result_message_key)
            self.result.text = f"[b]{message}[/b]"

    def logout(self):
        access_token = None
        if self.session:
            access_token = self.session.get("access_token")

        if access_token:
            try:
                sign_out(access_token)
            except RequestException as error:
                print(f"Logout Supabase fallito: {error}")
            else:
                print("Logout Supabase riuscito")

        clear_refresh_token(self.user_data_dir)
        self.session = None
        self.token_refresh_at = None
        self.food_lists = []
        self.clear_active_food_list()
        self.root.current = "auth"

    def logout_from_menu(self, instance):
        self.menu.dismiss()
        self.logout()

    def choose_food(self, instance):
        self.set_selected_food(None)

        if not self.current_list_id:
            self.result_message_key = "create_list_first"
            message = translate(self.language, self.result_message_key)
            self.result.text = f"[b]{message}[/b]"
            return

        if not self.food:
            self.result_message_key = "add_food_first"
            message = translate(self.language, self.result_message_key)
            self.result.text = f"[b]{message}[/b]"
            return

        # Keep the dish separately from its formatted display text.
        self.set_selected_food(random.choice(self.food))
        self.result_message_key = None
        self.result.text = f"[b]{self.selected_food}[/b]"


if __name__ == "__main__":  # pragma: no cover
    FoodApp().run()
