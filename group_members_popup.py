from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from requests import RequestException

from supabase_client import (
    add_group_member,
    get_group_members,
    remove_group_member,
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


def show_group_members_popup(group):
    app = App.get_running_app()
    language = getattr(app, "language", "it")
    is_owner = group["owner_id"] == app.get_user_id()
    members = []

    layout = BoxLayout(
        orientation="vertical",
        spacing=dp(8),
        padding=dp(12),
    )
    add_colored_background(layout)

    members_scroll = ScrollView(
        do_scroll_x=False,
        size_hint_y=1,
    )
    members_container = BoxLayout(
        orientation="vertical",
        spacing=dp(6),
        size_hint_y=None,
    )
    members_container.bind(
        minimum_height=members_container.setter("height")
    )
    members_scroll.add_widget(members_container)

    status = Label(
        text="",
        font_size=sp(13),
        size_hint_y=None,
        height=dp(34),
        color=(0.55, 0.15, 0.15, 1),
    )

    layout.add_widget(members_scroll)

    if is_owner:
        add_controls = BoxLayout(
            orientation="horizontal",
            spacing=dp(7),
            size_hint_y=None,
            height=dp(44),
        )

        email_input = TextInput(
            hint_text=translate(language, "member_email_hint"),
            multiline=False,
            font_size=sp(14),
            padding=(dp(8), dp(8)),
        )

        add_button = RoundedButton(
            text=translate(language, "add"),
            font_size=sp(13),
            size_hint_x=0.35,
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        add_controls.add_widget(email_input)
        add_controls.add_widget(add_button)
        layout.add_widget(add_controls)

    layout.add_widget(status)

    close_button = RoundedButton(
        text=translate(language, "close"),
        font_size=sp(15),
        size_hint_y=None,
        height=dp(44),
        my_color=(0.40, 0.40, 0.40, 1),
        color=(1, 1, 1, 1),
    )
    layout.add_widget(close_button)

    popup = Popup(
        title=translate(language, "members_popup_title", name=group["name"]),
        title_size=sp(19),
        content=layout,
        size_hint=(0.90, None),
        height=dp(430 if is_owner else 370),
        background="",
        background_color=POPUP_COLOR,
        title_color=TEXT_COLOR,
        separator_color=(0.10, 0.55, 0.45, 1),
    )

    def error_message(error, default):
        if error.response is None:
            return default

        try:
            message = error.response.json().get("message", "").lower()
        except ValueError:
            return default

        if "already a member" in message:
            return translate(language, "member_already_exists")
        if "user not found" in message:
            return translate(language, "member_not_found")
        if "only the group owner" in message:
            return translate(language, "owner_only_add_members")

        return default

    def refresh_members():
        nonlocal members

        try:
            members = get_group_members(
                group["id"],
                app.get_access_token(),
            )
        except RequestException:
            status.text = translate(language, "load_members_failed")
            return

        members_container.clear_widgets()

        for member in members:
            row = BoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint_y=None,
                height=dp(44),
            )

            role_text = translate(
                language,
                "owner_role" if member["role"] == "owner" else "member_role",
            )
            member_label = Label(
                text=f"{member['email']}\n{role_text}",
                font_size=sp(13),
                halign="left",
                valign="middle",
                color=TEXT_COLOR,
            )
            member_label.bind(
                size=lambda instance, value: setattr(
                    instance,
                    "text_size",
                    value,
                )
            )
            row.add_widget(member_label)

            if is_owner and member["role"] != "owner":
                remove_button = RoundedButton(
                    text=translate(language, "remove"),
                    font_size=sp(12),
                    size_hint_x=0.30,
                    my_color=(0.65, 0.18, 0.18, 1),
                    color=(1, 1, 1, 1),
                )
                remove_button.bind(
                    on_release=lambda instance,
                    selected_member=member: remove_member(
                        selected_member
                    )
                )
                row.add_widget(remove_button)

            members_container.add_widget(row)

        status.text = ""

    def remove_member(member):
        try:
            remove_group_member(
                group["id"],
                member["user_id"],
                app.get_access_token(),
            )
        except RequestException as error:
            status.text = error_message(
                error,
                translate(language, "remove_member_failed"),
            )
            return

        refresh_members()

    if is_owner:
        def add_member(instance):
            email = email_input.text.strip().lower()

            if not email:
                status.text = translate(language, "email_required")
                return

            if any(
                member["email"].strip().casefold()
                == email.casefold()
                for member in members
            ):
                status.text = translate(language, "member_already_exists")
                return

            try:
                add_group_member(
                    group["id"],
                    email,
                    app.get_access_token(),
                )
            except RequestException as error:
                status.text = error_message(
                    error,
                    translate(language, "add_member_failed"),
                )
                return

            email_input.text = ""
            refresh_members()

        add_button.bind(on_release=add_member)

    close_button.bind(on_release=popup.dismiss)
    refresh_members()
    popup.open()
