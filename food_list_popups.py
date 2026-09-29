from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from requests import RequestException

from supabase_client import (
    create_food_list,
    create_group,
    create_group_food_list,
    delete_food_list,
    delete_group,
    remove_group_member,
    rename_food_list,
    rename_group,
)
from translations import translate
from ui_components import RoundedButton

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


class FoodListPopupsMixin:
    def open_create_popup(self, instance, shared=False):
        self.status_label.text = ""
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=(dp(14), dp(10), dp(14), dp(2)),
        )
        add_colored_background(layout)

        name_input = TextInput(
            hint_text=translate(
                self.language,
                "shared_list_name" if shared else "personal_list_name",
            ),
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
            text=translate(self.language, "create"),
            size_hint_y=None,
            height=dp(42),
            my_color=(
                (0.25, 0.55, 0.70, 1)
                if shared
                else (0.10, 0.55, 0.45, 1)
            ),
            color=(1, 1, 1, 1),
        )

        layout.add_widget(name_input)
        layout.add_widget(status)
        layout.add_widget(create_button)

        popup = Popup(
            title=translate(
                self.language,
                "create_shared_list" if shared else "create_personal_list",
            ),
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
                status.text = translate(self.language, "list_name_required")
                return

            if any(
                food_list["name"].strip().casefold()
                == list_name.casefold()
                for food_list in app.food_lists
            ):
                status.text = translate(self.language, "duplicate_list_name")
                return

            created_group = None

            try:
                if shared:
                    created_group = create_group(
                        list_name,
                        app.get_user_id(),
                        app.get_access_token(),
                    )
                    created_list = create_group_food_list(
                        list_name,
                        created_group["id"],
                        app.get_access_token(),
                    )
                else:
                    created_list = create_food_list(
                        list_name,
                        app.get_user_id(),
                        app.get_access_token(),
                    )
            except RequestException:
                if created_group:
                    try:
                        delete_group(
                            created_group["id"],
                            app.get_access_token(),
                        )
                    except RequestException:
                        pass

                status.text = translate(self.language, "create_list_failed")
                return

            if created_group:
                self.groups.append(created_group)

            app.food_lists.append(created_list)
            app.select_food_list(created_list)
            self.selected_list_id = created_list["id"]
            self.status_label.text = ""
            status.text = ""
            self.render_lists()
            popup.dismiss()

        create_button.bind(on_release=create_list)
        popup.open()

    def open_rename_popup(self, instance):
        food_list = self.get_selected_list()

        if not food_list:
            return

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            padding=(dp(14), dp(10), dp(14), dp(2)),
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
            text=translate(self.language, "save"),
            size_hint_y=None,
            height=dp(42),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        layout.add_widget(name_input)
        layout.add_widget(status)
        layout.add_widget(save_button)

        popup = Popup(
            title=translate(self.language, "rename_list"),
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
                status.text = translate(self.language, "new_name_required")
                return

            if any(
                existing["id"] != food_list["id"]
                and existing["name"].strip().casefold()
                == new_name.casefold()
                for existing in app.food_lists
            ):
                status.text = translate(self.language, "duplicate_list_name")
                return

            try:
                rename_food_list(
                    food_list["id"],
                    new_name,
                    app.get_access_token(),
                )

                group = self.get_group_for_list(food_list)
                if group:
                    rename_group(
                        group["id"],
                        new_name,
                        app.get_access_token(),
                    )
            except RequestException:
                status.text = translate(self.language, "rename_list_failed")
                return

            food_list["name"] = new_name
            group = self.get_group_for_list(food_list)
            if group:
                group["name"] = new_name

            if app.current_list_id == food_list["id"]:
                app.current_list_name = new_name
                app.active_list_label.text = translate(
                    self.language, "active_list", name=new_name
                )

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

        message_key = (
            "delete_shared_confirm"
            if food_list.get("group_id") is not None
            else "delete_personal_confirm"
        )
        message = Label(
            text=translate(
                self.language,
                message_key,
                name=food_list["name"],
            ),
            color=(0.08, 0.25, 0.20, 1),
        )
        message.halign = "center"
        message.valign = "middle"
        message.bind(
            width=lambda label, width: setattr(
                label, "text_size", (width, None)
            )
        )

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        cancel_button = RoundedButton(
            text=translate(self.language, "cancel"),
            my_color=(0.40, 0.40, 0.40, 1),
            color=(1, 1, 1, 1),
        )
        confirm_button = RoundedButton(
            text=translate(self.language, "delete"),
            my_color=(0.65, 0.18, 0.18, 1),
            color=(1, 1, 1, 1),
        )

        buttons.add_widget(cancel_button)
        buttons.add_widget(confirm_button)
        layout.add_widget(message)
        layout.add_widget(buttons)

        popup = Popup(
            title=translate(self.language, "confirm_deletion"),
            title_size=sp(21),
            content=layout,
            size_hint=(0.80, None),
            height=dp(280),
            background="",
            background_color=POPUP_COLOR,
            title_color=TEXT_COLOR,
            separator_color=(0.10, 0.55, 0.45, 1),
        )

        def confirm_deletion(button):
            app = App.get_running_app()
            group = self.get_group_for_list(food_list)

            try:
                if group:
                    delete_group(
                        group["id"],
                        app.get_access_token(),
                    )
                else:
                    delete_food_list(
                        food_list["id"],
                        app.get_access_token(),
                    )
            except RequestException:
                message.text = translate(
                    self.language, "delete_list_failed"
                )
                return

            app.food_lists = [
                existing
                for existing in app.food_lists
                if existing["id"] != food_list["id"]
            ]

            if group:
                self.groups = [
                    existing
                    for existing in self.groups
                    if existing["id"] != group["id"]
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

    def open_leave_popup(self, instance):
        food_list = self.get_selected_list()

        if not food_list:
            return

        group = self.get_group_for_list(food_list)

        if not group:
            self.status_label.text = translate(
                self.language, "leave_shared_unavailable"
            )
            return

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
        )
        add_colored_background(layout)

        message = Label(
            text=translate(
                self.language,
                "leave_shared_confirm",
                name=food_list["name"],
            ),
            color=(0.08, 0.25, 0.20, 1),
        )
        message.halign = "center"
        message.valign = "middle"
        message.bind(
            width=lambda label, width: setattr(
                label, "text_size", (width, None)
            )
        )

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        cancel_button = RoundedButton(
            text=translate(self.language, "cancel"),
            my_color=(0.40, 0.40, 0.40, 1),
            color=(1, 1, 1, 1),
        )
        confirm_button = RoundedButton(
            text=translate(self.language, "leave"),
            my_color=(0.65, 0.18, 0.18, 1),
            color=(1, 1, 1, 1),
        )

        buttons.add_widget(cancel_button)
        buttons.add_widget(confirm_button)
        layout.add_widget(message)
        layout.add_widget(buttons)

        popup = Popup(
            title=translate(self.language, "leave_shared_title"),
            title_size=sp(19),
            content=layout,
            size_hint=(0.80, None),
            height=dp(280),
            background="",
            background_color=POPUP_COLOR,
            title_color=TEXT_COLOR,
            separator_color=(0.10, 0.55, 0.45, 1),
        )

        def confirm_leave(button):
            app = App.get_running_app()

            try:
                remove_group_member(
                    group["id"],
                    app.get_user_id(),
                    app.get_access_token(),
                )
            except RequestException:
                message.text = translate(
                    self.language, "leave_list_failed"
                )
                return

            app.food_lists = [
                existing
                for existing in app.food_lists
                if existing["id"] != food_list["id"]
            ]
            self.groups = [
                existing
                for existing in self.groups
                if existing["id"] != group["id"]
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
        confirm_button.bind(on_release=confirm_leave)
        popup.open()
