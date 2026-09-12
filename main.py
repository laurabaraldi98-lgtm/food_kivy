import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from requests import RequestException

from auth_client import sign_out
from auth_screen import AuthScreen
from food_lists_screen import FoodListsScreen
from signup_screen import SignUpScreen
from supabase_client import get_food_lists, get_foods
from ui_components import MenuButton, RoundedButton


if platform not in ("android", "ios"):
    Window.size = (360, 640)

if platform == "android":
    Window.softinput_mode = "below_target"

Window.clearcolor = (0.70, 0.92, 0.88, 1)
Window.set_icon("images/icon.png")


class FoodApp(App):
    def build(self):
        self.session = None
        self.food = []
        self.food_lists = []
        self.current_list_id = None
        self.current_list_name = ""

        home_screen = Screen(name="food")
        home_screen.add_widget(self.build_home())

        manager = ScreenManager()
        manager.add_widget(AuthScreen(name="auth"))
        manager.add_widget(SignUpScreen(name="signup"))
        manager.add_widget(home_screen)
        manager.add_widget(FoodListsScreen(name="food_lists"))
        manager.current = "auth"

        return manager

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
            text="Cosa mangiamo?",
            font_name="fonts/Pacifico-Regular.ttf",
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.79},
            color=(0.02, 0.35, 0.28, 1),
        )

        self.choose_button = RoundedButton(
            text="Scegli per me",
            size_hint=(0.74, None),
            pos_hint={"center_x": 0.5, "center_y": 0.62},
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.result = Label(
            text="",
            font_name="fonts/Pacifico-Regular.ttf",
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.48},
            color=(0.02, 0.35, 0.28, 1),
        )

        self.active_list_label = Label(
            text="Nessuna lista attiva",
            size_hint=(0.9, 0.08),
            pos_hint={"center_x": 0.5, "center_y": 0.34},
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

        lists_button = RoundedButton(
            text="Gestisci liste",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        lists_button.bind(on_release=self.open_food_lists_from_menu)

        logout_button = RoundedButton(
            text="Logout",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.55, 0.20, 0.20, 1),
            color=(1, 1, 1, 1),
        )
        logout_button.bind(on_release=self.logout_from_menu)

        self.menu.add_widget(lists_button)
        self.menu.add_widget(logout_button)
        self.menu_button.bind(on_release=self.menu.open)
        self.choose_button.bind(on_press=self.choose_food)

        root.add_widget(self.title_label)
        root.add_widget(self.choose_button)
        root.add_widget(self.result)
        root.add_widget(self.active_list_label)
        root.add_widget(self.menu_button)

        Window.bind(size=self.update_layout)
        Clock.schedule_once(self.update_layout, 0)

        return root

    def open_food_screen(self, session):
        self.session = session
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

    def select_food_list(self, food_list):
        self.current_list_id = food_list["id"]
        self.current_list_name = food_list["name"]
        self.food = get_foods(
            self.current_list_id,
            self.get_access_token(),
        )
        self.active_list_label.text = (
            f"Lista attiva: {self.current_list_name}"
        )
        self.result.text = ""

    def clear_active_food_list(self):
        self.current_list_id = None
        self.current_list_name = ""
        self.food = []
        self.active_list_label.text = "Nessuna lista attiva"
        self.result.text = ""

    def open_food_lists_from_menu(self, instance):
        self.menu.dismiss()
        self.root.current = "food_lists"

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

        self.session = None
        self.food_lists = []
        self.clear_active_food_list()
        self.root.current = "auth"

    def logout_from_menu(self, instance):
        self.menu.dismiss()
        self.logout()

    def update_layout(self, *args):
        self.choose_button.height = dp(52)
        self.choose_button.font_size = sp(20)
        self.title_label.font_size = sp(34)
        self.result.font_size = sp(30)
        self.active_list_label.font_size = sp(16)

    def get_access_token(self):
        if not self.session:
            raise RuntimeError("User is not authenticated")

        return self.session["access_token"]

    def get_user_id(self):
        if not self.session:
            raise RuntimeError("User is not authenticated")

        return self.session["user"]["id"]

    def choose_food(self, instance):
        if not self.current_list_id:
            self.result.text = "[b]Crea prima una lista[/b]"
            return

        if not self.food:
            self.result.text = "[b]Aggiungi prima qualche cibo[/b]"
            return

        self.result.text = f"[b]{random.choice(self.food)}[/b]"


FoodApp().run()
