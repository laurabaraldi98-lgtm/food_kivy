from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from requests import RequestException

from food_list_popups import FoodListPopupsMixin
from food_popup import show_food_popup
from group_members_popup import show_group_members_popup
from supabase_client import get_groups
from translations import translate
from ui_components import MenuButton, RoundedButton


TEXT_COLOR = (0.02, 0.35, 0.28, 1)


class FoodListsScreen(FoodListPopupsMixin, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_list_id = None
        self.groups = []
        self.language = "it"
        self.build_interface()

    def build_interface(self):
        root = FloatLayout()

        background = Image(
            source="images/background_tall.png",
            fit_mode="cover",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        root.add_widget(background)

        self.title_label = Label(
            text="Le mie liste",
            font_name="fonts/Pacifico-Regular.ttf",
            font_size=sp(34),
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.79},
            color=TEXT_COLOR,
        )
        root.add_widget(self.title_label)

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

        self.home_button = RoundedButton(
            text="Torna alla Home",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        self.home_button.bind(on_release=self.go_home_from_menu)

        self.language_button = RoundedButton(
            text="English",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.language_flag = Image(
            source="images/flag_en.png",
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
            text="Logout",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.55, 0.20, 0.20, 1),
            color=(1, 1, 1, 1),
        )
        self.logout_button.bind(on_release=self.logout_from_menu)

        self.menu.add_widget(self.home_button)
        self.menu.add_widget(self.language_button)
        self.menu.add_widget(self.logout_button)
        self.menu_button.bind(on_release=self.menu.open)
        root.add_widget(self.menu_button)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(18), dp(8)),
            size_hint=(0.92, 0.62),
            pos_hint={"center_x": 0.5, "y": 0.08},
        )

        create_buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        self.personal_button = RoundedButton(
            text="+ Personale",
            font_size=sp(15),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        self.personal_button.bind(
            on_release=lambda instance: self.open_create_popup(
                instance,
                shared=False,
            )
        )

        self.shared_button = RoundedButton(
            text="+ Condivisa",
            font_size=sp(15),
            my_color=(0.25, 0.55, 0.70, 1),
            color=(1, 1, 1, 1),
        )
        self.shared_button.bind(
            on_release=lambda instance: self.open_create_popup(
                instance,
                shared=True,
            )
        )

        create_buttons.add_widget(self.personal_button)
        create_buttons.add_widget(self.shared_button)

        self.status_label = Label(
            text="",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(28),
            color=(0.55, 0.15, 0.15, 1),
        )

        scroll = ScrollView(do_scroll_x=False)
        self.list_container = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )
        self.list_container.bind(
            minimum_height=self.list_container.setter("height")
        )
        scroll.add_widget(self.list_container)

        content.add_widget(create_buttons)
        content.add_widget(self.status_label)
        content.add_widget(scroll)
        root.add_widget(content)
        self.add_widget(root)

    def refresh_texts(self, language):
        self.language = language
        self.title_label.text = translate(language, "my_lists")
        self.home_button.text = translate(language, "back_home")
        self.logout_button.text = translate(language, "logout")
        self.personal_button.text = translate(
            language, "personal_list_button"
        )
        self.shared_button.text = translate(
            language, "shared_list_button"
        )
        self.language_button.text = (
            "Italiano" if language == "en" else "English"
        )
        self.language_flag.source = (
            "images/flag_it.png"
            if language == "en"
            else "images/flag_en.png"
        )

    def toggle_language(self, instance):
        self.menu.dismiss()
        app = App.get_running_app()
        next_language = "en" if app.language == "it" else "it"
        app.set_language(next_language)

    def on_pre_enter(self, *args):
        app = App.get_running_app()

        try:
            app.reload_food_lists()
            self.groups = get_groups(app.get_access_token())
        except RequestException:
            self.status_label.text = "Impossibile caricare le liste"
            return

        self.status_label.text = ""
        self.selected_list_id = None
        self.render_lists()

    def render_lists(self):
        app = App.get_running_app()
        self.list_container.clear_widgets()

        if not app.food_lists:
            self.list_container.add_widget(
                Label(
                    text=translate(self.language, "no_lists"),
                    font_size=sp(18),
                    size_hint_y=None,
                    height=dp(60),
                    color=TEXT_COLOR,
                )
            )
            return

        for food_list in app.food_lists:
            group = self.get_group_for_list(food_list)
            is_shared = food_list.get("group_id") is not None
            is_owner = bool(
                group and group["owner_id"] == app.get_user_id()
            )
            card = BoxLayout(
                orientation="vertical",
                spacing=dp(6),
                padding=dp(6),
                size_hint_y=None,
            )

            is_active = food_list["id"] == app.current_list_id
            is_selected = food_list["id"] == self.selected_list_id
            if is_selected and is_shared:
                card.height = dp(154)
            else:
                card.height = dp(104 if is_selected else 54)

            displayed_name = food_list["name"]
            if is_shared:
                shared_suffix = translate(self.language, "shared_suffix")
                displayed_name += f"  ({shared_suffix})"

            list_button = RoundedButton(
                text=(
                    f"*  {displayed_name}"
                    if is_active
                    else displayed_name
                ),
                size_hint_y=None,
                height=dp(48),
                font_size=sp(17),
                my_color=(
                    (0.10, 0.55, 0.45, 0.22)
                    if is_selected
                    else (0, 0, 0, 0)
                ),
                color=TEXT_COLOR,
            )
            list_button.bind(
                on_release=lambda instance,
                selected=food_list: self.select_list(selected)
            )
            card.add_widget(list_button)

            if is_selected:
                primary_actions = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(6),
                    size_hint_y=None,
                    height=dp(44),
                )

                view_button = RoundedButton(
                    text=translate(self.language, "view_foods"),
                    font_size=sp(13),
                    my_color=(0.10, 0.55, 0.45, 1),
                    color=(1, 1, 1, 1),
                )
                view_button.bind(on_release=self.open_selected_foods)
                primary_actions.add_widget(view_button)

                if is_shared:
                    members_button = RoundedButton(
                        text=translate(self.language, "members"),
                        font_size=sp(13),
                        my_color=(0.55, 0.42, 0.70, 1),
                        color=(1, 1, 1, 1),
                    )
                    members_button.bind(
                        on_release=self.open_members_popup
                    )
                    primary_actions.add_widget(members_button)

                secondary_actions = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(6),
                    size_hint_y=None,
                    height=dp(44),
                )

                rename_button = RoundedButton(
                    text=translate(self.language, "rename"),
                    font_size=sp(13),
                    my_color=(0.25, 0.55, 0.70, 1),
                    color=(1, 1, 1, 1),
                )
                rename_button.bind(on_release=self.open_rename_popup)

                final_button = RoundedButton(
                    text=translate(
                        self.language,
                        "leave" if is_shared and not is_owner else "delete",
                    ),
                    font_size=sp(13),
                    my_color=(0.65, 0.18, 0.18, 1),
                    color=(1, 1, 1, 1),
                )
                if is_shared and not is_owner:
                    final_button.bind(
                        on_release=self.open_leave_popup
                    )
                else:
                    final_button.bind(
                        on_release=self.open_delete_popup
                    )

                if is_shared:
                    secondary_actions.add_widget(rename_button)
                    secondary_actions.add_widget(final_button)
                    card.add_widget(primary_actions)
                    card.add_widget(secondary_actions)
                else:
                    primary_actions.add_widget(rename_button)
                    primary_actions.add_widget(final_button)
                    card.add_widget(primary_actions)

            self.list_container.add_widget(card)

    def select_list(self, food_list):
        app = App.get_running_app()

        if self.selected_list_id == food_list["id"]:
            self.selected_list_id = None
            self.render_lists()
            return

        try:
            app.select_food_list(food_list)
        except RequestException:
            self.status_label.text = "Impossibile caricare i cibi"
            return

        self.selected_list_id = food_list["id"]
        self.status_label.text = ""
        self.render_lists()

    def get_selected_list(self):
        app = App.get_running_app()
        return next(
            (
                food_list
                for food_list in app.food_lists
                if food_list["id"] == self.selected_list_id
            ),
            None,
        )

    def get_group_for_list(self, food_list):
        group_id = food_list.get("group_id")

        if group_id is None:
            return None

        return next(
            (
                group
                for group in self.groups
                if group["id"] == group_id
            ),
            None,
        )

    def open_selected_foods(self, instance):
        if not self.get_selected_list():
            return

        show_food_popup(App.get_running_app())

    def open_members_popup(self, instance):
        food_list = self.get_selected_list()

        if not food_list:
            return

        group = self.get_group_for_list(food_list)

        if not group:
            self.status_label.text = "Impossibile aprire i membri della lista"
            return

        self.status_label.text = ""
        show_group_members_popup(group)

    def go_home_from_menu(self, instance):
        self.menu.dismiss()
        App.get_running_app().root.current = "food"

    def logout_from_menu(self, instance):
        self.menu.dismiss()
        App.get_running_app().logout()
