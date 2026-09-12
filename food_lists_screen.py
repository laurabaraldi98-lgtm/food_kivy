from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from requests import RequestException

from food_popup import show_food_popup
from supabase_client import (
    create_food_list,
    delete_food_list,
    rename_food_list,
)
from ui_components import MenuButton, RoundedButton


POPUP_COLOR = (0.70, 0.92, 0.88, 1)
TEXT_COLOR = (0.02, 0.35, 0.28, 1)


def add_colored_background(widget):
    with widget.canvas.before:
        Color(*POPUP_COLOR)
        background = Rectangle(
            size=widget.size,
            pos=widget.pos,
        )

    def update_background(instance, value):
        background.size = instance.size
        background.pos = instance.pos

    widget.bind(
        size=update_background,
        pos=update_background,
    )


class FoodListsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_list_id = None
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

        title = Label(
            text="Le mie liste",
            font_name="fonts/Pacifico-Regular.ttf",
            font_size=sp(34),
            size_hint=(0.9, 0.10),
            pos_hint={"center_x": 0.5, "center_y": 0.79},
            color=TEXT_COLOR,
        )
        root.add_widget(title)

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

        home_button = RoundedButton(
            text="Torna alla Home",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        home_button.bind(on_release=self.go_home_from_menu)

        logout_button = RoundedButton(
            text="Logout",
            font_size=sp(17),
            size_hint_y=None,
            height=dp(48),
            my_color=(0.55, 0.20, 0.20, 1),
            color=(1, 1, 1, 1),
        )
        logout_button.bind(on_release=self.logout_from_menu)

        self.menu.add_widget(home_button)
        self.menu.add_widget(logout_button)
        self.menu_button.bind(on_release=self.menu.open)
        root.add_widget(self.menu_button)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(18), dp(8)),
            size_hint=(0.92, 0.62),
            pos_hint={"center_x": 0.5, "y": 0.08},
        )

        create_button = RoundedButton(
            text="+ Nuova lista",
            size_hint_y=None,
            height=dp(48),
            font_size=sp(17),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        create_button.bind(on_release=self.open_create_popup)

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

        content.add_widget(create_button)
        content.add_widget(self.status_label)
        content.add_widget(scroll)
        root.add_widget(content)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        app = App.get_running_app()

        try:
            app.reload_food_lists()
        except RequestException:
            self.status_label.text = "Impossibile caricare le liste"
            return

        self.selected_list_id = None
        self.render_lists()

    def render_lists(self):
        app = App.get_running_app()
        self.list_container.clear_widgets()

        if not app.food_lists:
            self.list_container.add_widget(
                Label(
                    text="Non hai ancora nessuna lista",
                    font_size=sp(18),
                    size_hint_y=None,
                    height=dp(60),
                    color=(0.02, 0.35, 0.28, 1),
                )
            )
            return

        for food_list in app.food_lists:
            card = BoxLayout(
                orientation="vertical",
                spacing=dp(6),
                padding=dp(6),
                size_hint_y=None,
            )

            is_selected = food_list["id"] == self.selected_list_id
            card.height = dp(104 if is_selected else 54)

            list_button = RoundedButton(
                text=food_list["name"],
                size_hint_y=None,
                height=dp(48),
                font_size=sp(17),
                my_color=(
                    (0.06, 0.42, 0.34, 1)
                    if is_selected
                    else (0.10, 0.55, 0.45, 1)
                ),
                color=(1, 1, 1, 1),
            )
            list_button.bind(
                on_release=lambda instance,
                selected=food_list: self.select_list(selected)
            )
            card.add_widget(list_button)

            if is_selected:
                actions = BoxLayout(
                    orientation="horizontal",
                    spacing=dp(6),
                    size_hint_y=None,
                    height=dp(44),
                )

                view_button = RoundedButton(
                    text="Vedi cibi",
                    font_size=sp(13),
                    my_color=(0.10, 0.55, 0.45, 1),
                    color=(1, 1, 1, 1),
                )
                view_button.bind(on_release=self.open_selected_foods)

                rename_button = RoundedButton(
                    text="Rinomina",
                    font_size=sp(13),
                    my_color=(0.25, 0.55, 0.70, 1),
                    color=(1, 1, 1, 1),
                )
                rename_button.bind(on_release=self.open_rename_popup)

                delete_button = RoundedButton(
                    text="Elimina",
                    font_size=sp(13),
                    my_color=(0.65, 0.18, 0.18, 1),
                    color=(1, 1, 1, 1),
                )
                delete_button.bind(on_release=self.open_delete_popup)

                actions.add_widget(view_button)
                actions.add_widget(rename_button)
                actions.add_widget(delete_button)
                card.add_widget(actions)

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

    def open_create_popup(self, instance):
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=(
                dp(14),
                dp(10),
                dp(14),
                dp(2),
            ),
        )
        add_colored_background(layout)

        name_input = TextInput(
            hint_text="Nome nuova lista",
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size=sp(15),
            padding=(dp(7), dp(7)),
        )
        status = Label(
            text="",
            size_hint_y=None,
            height=dp(16),
            font_size=sp(12),
            color=(0.55, 0.15, 0.15, 1),
        )
        create_button = RoundedButton(
            text="Crea",
            size_hint_y=None,
            height=dp(42),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        layout.add_widget(name_input)
        layout.add_widget(status)
        layout.add_widget(create_button)

        popup = Popup(
            title="Crea nuova lista",
            title_size=sp(19),
            content=layout,
            size_hint=(0.78, None),
            height=dp(195),
            background="",
            background_color=POPUP_COLOR,
            title_color=TEXT_COLOR,
            separator_color=(0.10, 0.55, 0.45, 1),
        )

        def create_list(button):
            app = App.get_running_app()
            list_name = name_input.text.strip()

            if not list_name:
                status.text = "Inserisci un nome per la lista"
                return

            if any(
                food_list["name"].strip().casefold()
                == list_name.casefold()
                for food_list in app.food_lists
            ):
                status.text = "Esiste già una lista con questo nome"
                return

            try:
                created_list = create_food_list(
                    list_name,
                    app.get_user_id(),
                    app.get_access_token(),
                )
                app.food_lists.append(created_list)
                app.select_food_list(created_list)
            except RequestException:
                status.text = "Impossibile creare la lista"
                return

            self.selected_list_id = None
            self.status_label.text = ""
            popup.dismiss()
            self.render_lists()

        create_button.bind(on_release=create_list)
        popup.open()

    def open_selected_foods(self, instance):
        if not self.get_selected_list():
            return

        show_food_popup(App.get_running_app())

    def open_rename_popup(self, instance):
        food_list = self.get_selected_list()

        if not food_list:
            return

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=(
                dp(14),
                dp(10),
                dp(14),
                dp(2),
            ),
        )
        add_colored_background(layout)
        name_input = TextInput(
            text=food_list["name"],
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size=sp(15),
            padding=(dp(7), dp(7)),
        )
        status = Label(
            text="",
            size_hint_y=None,
            height=dp(16),
            font_size=sp(12),
            color=(0.55, 0.15, 0.15, 1),
        )
        save_button = RoundedButton(
            text="Salva",
            size_hint_y=None,
            height=dp(42),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        layout.add_widget(name_input)
        layout.add_widget(status)
        layout.add_widget(save_button)

        popup = Popup(
            title="Rinomina lista",
            title_size=sp(19),
            content=layout,
            size_hint=(0.78, None),
            height=dp(195),
            background="",
            background_color=POPUP_COLOR,
            title_color=TEXT_COLOR,
            separator_color=(0.10, 0.55, 0.45, 1),
        )

        def save_name(button):
            app = App.get_running_app()
            new_name = name_input.text.strip()

            if not new_name:
                status.text = "Inserisci un nuovo nome"
                return

            if any(
                existing["id"] != food_list["id"]
                and existing["name"].strip().casefold()
                == new_name.casefold()
                for existing in app.food_lists
            ):
                status.text = "Esiste già una lista con questo nome"
                return

            try:
                rename_food_list(
                    food_list["id"],
                    new_name,
                    app.get_access_token(),
                )
            except RequestException:
                status.text = "Impossibile rinominare la lista"
                return

            food_list["name"] = new_name
            if app.current_list_id == food_list["id"]:
                app.current_list_name = new_name
                app.active_list_label.text = f"Lista attiva: {new_name}"

            popup.dismiss()
            self.render_lists()

        save_button.bind(on_release=save_name)
        popup.open()

    def open_delete_popup(self, instance):
        food_list = self.get_selected_list()

        if not food_list:
            return

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
        )
        add_colored_background(layout)
        message = Label(
            text=(
                f"Eliminare la lista '{food_list['name']}'?\n"
                "Verranno eliminati anche i suoi cibi."
            ),
            color=(0.08, 0.25, 0.20, 1),
        )
        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )
        cancel_button = RoundedButton(
            text="Annulla",
            my_color=(0.40, 0.40, 0.40, 1),
            color=(1, 1, 1, 1),
        )
        confirm_button = RoundedButton(
            text="Elimina",
            my_color=(0.65, 0.18, 0.18, 1),
            color=(1, 1, 1, 1),
        )
        buttons.add_widget(cancel_button)
        buttons.add_widget(confirm_button)
        layout.add_widget(message)
        layout.add_widget(buttons)

        popup = Popup(
            title="Conferma eliminazione",
            title_size=sp(21),
            content=layout,
            size_hint=(0.80, None),
            height=dp(210),
            background="",
            background_color=POPUP_COLOR,
            title_color=TEXT_COLOR,
            separator_color=(0.10, 0.55, 0.45, 1),
        )

        def confirm_deletion(button):
            app = App.get_running_app()

            try:
                delete_food_list(
                    food_list["id"],
                    app.get_access_token(),
                )
            except RequestException:
                message.text = "Impossibile eliminare la lista"
                return

            app.food_lists = [
                existing
                for existing in app.food_lists
                if existing["id"] != food_list["id"]
            ]

            if app.current_list_id == food_list["id"]:
                if app.food_lists:
                    app.select_food_list(app.food_lists[0])
                else:
                    app.clear_active_food_list()

            self.selected_list_id = None
            popup.dismiss()
            self.render_lists()

        cancel_button.bind(on_release=popup.dismiss)
        confirm_button.bind(on_release=confirm_deletion)
        popup.open()

    def go_home_from_menu(self, instance):
        self.menu.dismiss()
        App.get_running_app().root.current = "food"

    def logout_from_menu(self, instance):
        self.menu.dismiss()
        App.get_running_app().logout()
