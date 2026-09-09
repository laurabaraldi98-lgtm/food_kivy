from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from requests import RequestException

from auth_client import sign_in
from ui_components import RoundedButton


class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        background = Image(
            source=self.get_background_source(),
            fit_mode="cover",
            size_hint=(1, 1),
        )

        self.add_widget(background)

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.74, None),
            height=dp(390),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.52,
            },
        )

        title = Label(
            text="Cosa mangiamo?",
            font_name="fonts/Pacifico-Regular.ttf",
            font_size=sp(34),
            color=(0.02, 0.35, 0.28, 1),
            size_hint_y=None,
            height=dp(60),
        )

        self.email_input = TextInput(
            hint_text="Email",
            multiline=False,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(46),
            padding=(dp(10), dp(10)),
        )

        self.password_input = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(46),
            padding=(dp(10), dp(10)),
        )

        sign_in_button = RoundedButton(
            text="Accedi",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(52),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        account_prompt = Label(
            text="Non hai ancora un account?",
            font_size=sp(14),
            color=(0.02, 0.35, 0.28, 1),
            size_hint_y=None,
            height=dp(26),
        )

        sign_up_button = RoundedButton(
            text="Creane uno",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(52),
            my_color=(0.22, 0.68, 0.48, 1),
            color=(1, 1, 1, 1),
        )

        self.status_label = Label(
            text="",
            font_size=sp(14),
            color=(0.55, 0.20, 0.20, 1),
            size_hint_y=None,
            height=dp(34),
        )

        sign_in_button.bind(
            on_press=self.handle_sign_in
        )

        sign_up_button.bind(
            on_press=self.open_sign_up
        )

        form.add_widget(title)
        form.add_widget(self.email_input)
        form.add_widget(self.password_input)
        form.add_widget(sign_in_button)
        form.add_widget(account_prompt)
        form.add_widget(sign_up_button)
        form.add_widget(self.status_label)

        self.add_widget(form)

    def get_background_source(self):
        ratio = Window.width / Window.height

        if ratio < 0.48:
            return "images/background_tall.png"

        return "images/background.png"

    def get_credentials(self):
        email = self.email_input.text.strip().lower()
        password = self.password_input.text

        if not email or not password:
            self.status_label.text = (
                "Inserisci email e password"
            )
            return None

        return email, password

    def handle_sign_in(self, instance):
        credentials = self.get_credentials()

        if credentials is None:
            return

        email, password = credentials

        try:
            session = sign_in(email, password)
        except RequestException:
            self.status_label.text = (
                "Email o password non corretti"
            )
            return

        app = App.get_running_app()

        self.status_label.text = ""
        app.open_food_screen(session)

    def open_sign_up(self, instance):
        self.status_label.text = ""
        self.manager.current = "signup"
