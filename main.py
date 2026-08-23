from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.utils import platform

from supabase_client import get_foods, add_food, delete_food

import random


if platform not in ("android", "ios"):
    Window.size = (360, 640)

Window.clearcolor = (0.70, 0.92, 0.88, 1)


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


class RoundedButton(Button):
    def __init__(self, my_color=(0.10, 0.55, 0.45, 1), **kwargs):
        super().__init__(**kwargs)

        self.my_color = my_color
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)

        with self.canvas.before:
            self.button_color = Color(*self.my_color)
            self.rounded_rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[18]
            )

        self.bind(pos=self.update_rounded_rect)
        self.bind(size=self.update_rounded_rect)

    def update_rounded_rect(self, instance, value):
        self.rounded_rect.pos = self.pos
        self.rounded_rect.size = self.size


class FoodApp(App):
    def build(self):
        self.food = self.load_food()

        root = FloatLayout()

        background = Image(
            source="images/background.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )

        root.add_widget(background)

        self.title_label = Label(
            text="Cosa mangiamo?",
            font_name="fonts/Pacifico-Regular.ttf",
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.74
            },
            color=(0.02, 0.35, 0.28, 1)
        )

        self.choose_button = RoundedButton(
            text="Scegli per me",
            size_hint=(0.80, None),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.65
            },
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1)
        )

        self.result = Label(
            text="",
            font_name="fonts/Pacifico-Regular.ttf",
            markup=True,
            size_hint=(0.9, 0.10),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.51
            },
            color=(0.02, 0.35, 0.28, 1)
        )

        self.list_button = RoundedButton(
            text="Vedi lista cibi",
            size_hint=(0.80, None),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.37
            },
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1)
        )

        self.choose_button.bind(on_press=self.choose_food)
        self.list_button.bind(on_press=self.show_food_list)

        root.add_widget(self.title_label)
        root.add_widget(self.choose_button)
        root.add_widget(self.result)
        root.add_widget(self.list_button)

        Window.bind(size=self.update_layout)
        Clock.schedule_once(self.update_layout, 0)

        return root

    def update_layout(self, *args):
        height = Window.height

        button_height = clamp(height * 0.045, 28, 62)
        button_font = clamp(height * 0.023, 15, 31)
        title_font = clamp(height * 0.036, 23, 48)
        result_font = clamp(height * 0.034, 21, 44)

        self.choose_button.height = button_height
        self.list_button.height = button_height

        self.choose_button.font_size = button_font
        self.list_button.font_size = button_font

        self.title_label.font_size = title_font
        self.result.font_size = result_font

    def load_food(self):
        return get_foods()

    def choose_food(self, instance):
        if not self.food:
            self.result.text = "[b]Aggiungi prima qualche cibo[/b]"
            return

        choice = random.choice(self.food)
        self.result.text = f"[b]{choice}[/b]"

    def show_food_list(self, instance):
        food_text = "\n".join(self.food)

        popup_layout = FloatLayout()

        with popup_layout.canvas.before:
            Color(0.70, 0.92, 0.88, 1)
            rect = Rectangle(
                size=popup_layout.size,
                pos=popup_layout.pos
            )

        def update_rect(instance, value):
            rect.size = instance.size
            rect.pos = instance.pos

        popup_layout.bind(
            size=update_rect,
            pos=update_rect
        )

        label = Label(
            text=food_text,
            color=(0.02, 0.35, 0.28, 1),
            size_hint=(1, None)
        )

        def update_label_height(label, size):
            label.height = size[1]

        label.bind(texture_size=update_label_height)

        scroll = ScrollView(
            size_hint=(0.90, 0.25),
            pos_hint={
                "center_x": 0.5,
                "top": 0.97
            }
        )

        scroll.add_widget(label)

        form_layout = BoxLayout(
            orientation="vertical",
            spacing=4,
            size_hint=(0.88, 0.25),
            pos_hint={
                "center_x": 0.5,
                "y": 0.06
            }
        )

        add_input = TextInput(
            hint_text="Scrivi cibo da aggiungere",
            multiline=False,
            size_hint_y=None
        )

        add_popup_button = Button(
            text="Aggiungi cibo",
            size_hint_y=None,
            background_normal="",
            background_color=(0.22, 0.68, 0.48, 1),
            color=(1, 1, 1, 1)
        )

        delete_input = TextInput(
            hint_text="Scrivi cibo da eliminare",
            multiline=False,
            size_hint_y=None
        )

        delete_button = Button(
            text="Elimina cibo",
            size_hint_y=None,
            background_normal="",
            background_color=(0.55, 0.20, 0.20, 1),
            color=(1, 1, 1, 1)
        )

        status_label = Label(
            text="",
            color=(0.02, 0.35, 0.28, 1),
            size_hint_y=None
        )

        form_layout.add_widget(add_input)
        form_layout.add_widget(add_popup_button)
        form_layout.add_widget(delete_input)
        form_layout.add_widget(delete_button)
        form_layout.add_widget(status_label)

        def clear_status(dt):
            status_label.text = ""

        def refresh_list():
            label.text = "\n".join(self.food)

        def add_food_from_popup(instance):
            new_food = add_input.text.strip()

            if new_food:
                new_food = new_food[0].upper() + new_food[1:]

                if new_food not in self.food:
                    add_food(new_food)

                    self.food.append(new_food)
                    refresh_list()
                    status_label.text = f"Aggiunto: {new_food}"
                else:
                    status_label.text = f"{new_food} è già nella lista"

                Clock.schedule_once(clear_status, 3)
                add_input.text = ""

        def delete_food_from_popup(instance):
            food_to_delete = delete_input.text.strip()

            if food_to_delete:
                food_to_delete = (
                    food_to_delete[0].upper()
                    + food_to_delete[1:]
                )

                if food_to_delete in self.food:
                    delete_food(food_to_delete)

                    self.food.remove(food_to_delete)
                    refresh_list()
                    status_label.text = f"Eliminato: {food_to_delete}"
                else:
                    status_label.text = (
                        f"{food_to_delete} non è nella lista"
                    )

                Clock.schedule_once(clear_status, 3)
                delete_input.text = ""

        add_popup_button.bind(
            on_press=add_food_from_popup
        )

        delete_button.bind(
            on_press=delete_food_from_popup
        )

        popup_layout.add_widget(scroll)
        popup_layout.add_widget(form_layout)

        popup = Popup(
            title="Cibi disponibili",
            content=popup_layout,
            size_hint=(0.90, 0.90),
            background="",
            background_color=(0.70, 0.92, 0.88, 1),
            title_color=(0.02, 0.35, 0.28, 1),
            separator_color=(0.10, 0.55, 0.45, 1)
        )

        def update_popup_layout(*args):
            width = popup.width
            height = popup.height

            control_height = clamp(height * 0.055, 34, 52)
            status_height = clamp(height * 0.040, 24, 36)

            add_input.height = control_height
            add_popup_button.height = control_height
            delete_input.height = control_height
            delete_button.height = control_height
            status_label.height = status_height

            label.font_size = clamp(height * 0.040, 20, 30)

            input_font = clamp(height * 0.033, 16, 24)
            button_font = clamp(height * 0.033, 16, 24)
            status_font = clamp(height * 0.028, 14, 20)
            title_font = clamp(height * 0.040, 20, 30)

            add_input.font_size = input_font
            delete_input.font_size = input_font

            add_popup_button.font_size = button_font
            delete_button.font_size = button_font

            status_label.font_size = status_font
            popup.title_size = title_font

            form_layout.spacing = clamp(height * 0.006, 3, 8)

            form_layout.height = (
                control_height * 4
                + status_height
                + form_layout.spacing * 4
            )

        popup.bind(size=update_popup_layout)

        popup.open()

        Clock.schedule_once(update_popup_layout, 0)


FoodApp().run()
