from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from requests import RequestException

from supabase_client import add_food, delete_food


def show_food_popup(app):
    popup_layout = BoxLayout(
        orientation="vertical",
        padding=(dp(18), dp(10), dp(18), dp(12)),
    )

    with popup_layout.canvas.before:
        Color(0.70, 0.92, 0.88, 1)
        rect = Rectangle(
            size=popup_layout.size,
            pos=popup_layout.pos,
        )

    def update_rect(instance, value):
        rect.size = instance.size
        rect.pos = instance.pos

    popup_layout.bind(size=update_rect, pos=update_rect)

    content_scroll = ScrollView(
        size_hint=(1, 1),
        do_scroll_x=False,
        do_scroll_y=True,
    )

    content_column = BoxLayout(
        orientation="vertical",
        spacing=dp(4),
        padding=(0, dp(8), 0, dp(8)),
        size_hint_y=None,
    )
    content_column.bind(
        minimum_height=content_column.setter("height")
    )

    label = Label(
        text="\n".join(app.food) or "Lista vuota",
        font_size=sp(22),
        color=(0.02, 0.35, 0.28, 1),
        size_hint_y=None,
        halign="left",
        valign="top",
    )

    def update_label_layout(instance, size):
        instance.text_size = (
            content_scroll.width - dp(20),
            None,
        )
        instance.height = instance.texture_size[1]

    label.bind(texture_size=update_label_layout)
    content_scroll.bind(
        width=lambda *args: update_label_layout(
            label,
            label.texture_size,
        )
    )
    content_column.add_widget(label)
    content_column.add_widget(
        Widget(size_hint_y=None, height=dp(8))
    )

    control_height = dp(36)
    status_height = dp(20)
    form_spacing = dp(4)

    form_layout = BoxLayout(
        orientation="vertical",
        spacing=form_spacing,
        size_hint_y=None,
    )
    form_layout.height = (
        control_height * 4
        + status_height
        + form_spacing * 4
    )

    add_input = TextInput(
        hint_text="Scrivi cibo da aggiungere",
        multiline=False,
        font_size=sp(15),
        size_hint_y=None,
        height=control_height,
        padding=(dp(6), dp(6)),
    )

    add_button = Button(
        text="Aggiungi cibo",
        font_size=sp(16),
        size_hint_y=None,
        height=control_height,
        background_normal="",
        background_color=(0.22, 0.68, 0.48, 1),
        color=(1, 1, 1, 1),
    )

    delete_input = TextInput(
        hint_text="Scrivi cibo da eliminare",
        multiline=False,
        font_size=sp(15),
        size_hint_y=None,
        height=control_height,
        padding=(dp(6), dp(6)),
    )

    delete_button = Button(
        text="Elimina cibo",
        font_size=sp(16),
        size_hint_y=None,
        height=control_height,
        background_normal="",
        background_color=(0.55, 0.20, 0.20, 1),
        color=(1, 1, 1, 1),
    )

    status_label = Label(
        text="",
        font_size=sp(13),
        color=(0.02, 0.35, 0.28, 1),
        size_hint_y=None,
        height=status_height,
    )

    form_layout.add_widget(add_input)
    form_layout.add_widget(add_button)
    form_layout.add_widget(delete_input)
    form_layout.add_widget(delete_button)
    form_layout.add_widget(status_label)
    content_column.add_widget(form_layout)
    content_column.add_widget(
        Widget(size_hint_y=None, height=dp(16))
    )

    content_scroll.add_widget(content_column)
    popup_layout.add_widget(content_scroll)

    def scroll_to_input(instance, focused):
        if not focused:
            return

        Clock.schedule_once(
            lambda dt: content_scroll.scroll_to(
                instance,
                padding=dp(16),
                animate=True,
            ),
            0.2,
        )

    add_input.bind(focus=scroll_to_input)
    delete_input.bind(focus=scroll_to_input)

    def clear_status(dt):
        status_label.text = ""

    def refresh_list():
        label.text = "\n".join(app.food) or "Lista vuota"

    def add_food_from_popup(instance):
        new_food = add_input.text.strip()

        if not new_food:
            status_label.text = "Scrivi un cibo da aggiungere"
            return

        new_food = new_food[0].upper() + new_food[1:]

        if any(
            food.casefold() == new_food.casefold()
            for food in app.food
        ):
            status_label.text = f"{new_food} è già nella lista"
        else:
            try:
                add_food(
                    new_food,
                    app.current_list_id,
                    app.get_access_token(),
                )
            except RequestException:
                status_label.text = "Impossibile aggiungere il cibo"
                return

            app.food.append(new_food)
            app.food.sort(key=str.casefold)
            refresh_list()
            status_label.text = f"Aggiunto: {new_food}"

        Clock.schedule_once(clear_status, 3)
        add_input.text = ""

    def delete_food_from_popup(instance):
        typed_name = delete_input.text.strip()

        if not typed_name:
            status_label.text = "Scrivi un cibo da eliminare"
            return

        food_to_delete = next(
            (
                food
                for food in app.food
                if food.casefold() == typed_name.casefold()
            ),
            None,
        )

        if not food_to_delete:
            status_label.text = f"{typed_name} non è nella lista"
        else:
            try:
                delete_food(
                    food_to_delete,
                    app.current_list_id,
                    app.get_access_token(),
                )
            except RequestException:
                status_label.text = "Impossibile eliminare il cibo"
                return

            app.food.remove(food_to_delete)
            refresh_list()
            status_label.text = f"Eliminato: {food_to_delete}"

        Clock.schedule_once(clear_status, 3)
        delete_input.text = ""

    add_button.bind(on_press=add_food_from_popup)
    delete_button.bind(on_press=delete_food_from_popup)

    popup = Popup(
        title=f"Cibi - {app.current_list_name}",
        title_size=sp(22),
        content=popup_layout,
        size_hint=(0.84, 0.84),
        background="",
        background_color=(0.70, 0.92, 0.88, 1),
        title_color=(0.02, 0.35, 0.28, 1),
        separator_color=(0.10, 0.55, 0.45, 1),
    )
    popup.open()
