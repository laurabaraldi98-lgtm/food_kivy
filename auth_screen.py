from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from requests import RequestException

from auth_client import request_password_reset, sign_in
from translations import translate
from ui_components import RoundedButton


class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.language = "it"
        self.status_key = None

        background = Image(
            source=self.get_background_source(),
            fit_mode="cover",
            size_hint=(1, 1),
        )
        self.add_widget(background)

        self.language_button = Button(
            text="",
            background_normal="images/flag_en.png",
            background_down="images/flag_en.png",
            background_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
            size_hint=(None, None),
            width=dp(48),
            height=dp(48),
            pos_hint={"right": 0.97, "top": 0.98},
        )
        self.language_button.bind(on_release=self.toggle_language)
        self.add_widget(self.language_button)

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.74, None),
            height=dp(430),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        )

        title = Label(
            text="Food App",
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

        self.sign_in_button = RoundedButton(
            text="Accedi",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(52),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.forgot_password_button = Button(
            text="Password dimenticata?",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(28),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(0.02, 0.35, 0.28, 1),
        )

        self.account_prompt = Label(
            text="Non hai ancora un account?",
            font_size=sp(14),
            color=(0.02, 0.35, 0.28, 1),
            size_hint_y=None,
            height=dp(26),
        )

        self.sign_up_button = RoundedButton(
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

        self.sign_in_button.bind(on_press=self.handle_sign_in)
        self.sign_up_button.bind(on_press=self.open_sign_up)
        self.forgot_password_button.bind(
            on_press=self.handle_password_reset
        )

        form.add_widget(title)
        form.add_widget(self.email_input)
        form.add_widget(self.password_input)
        form.add_widget(self.sign_in_button)
        form.add_widget(self.forgot_password_button)
        form.add_widget(self.account_prompt)
        form.add_widget(self.sign_up_button)
        form.add_widget(self.status_label)

        self.add_widget(form)

    def refresh_texts(self, language):
        self.language = language
        self.language_button.background_normal = (
            "images/flag_it.png" if language == "en" else "images/flag_en.png"
        )
        self.language_button.background_down = (
            self.language_button.background_normal
        )
        self.sign_in_button.text = translate(language, "sign_in")
        self.forgot_password_button.text = translate(
            language, "forgot_password"
        )
        self.account_prompt.text = translate(language, "no_account")
        self.sign_up_button.text = translate(language, "create_one")

        if self.status_key is not None:
            self.status_label.text = translate(language, self.status_key)

    def set_status(self, key):
        self.status_key = key
        self.status_label.text = (
            translate(self.language, key) if key is not None else ""
        )

    def toggle_language(self, instance):
        app = App.get_running_app()
        next_language = "en" if app.language == "it" else "it"
        app.set_language(next_language)

    def get_background_source(self):
        ratio = Window.width / Window.height

        if ratio < 0.48:
            return "images/background_tall.png"

        return "images/background.png"

    def get_credentials(self):
        email = self.email_input.text.strip().lower()
        password = self.password_input.text

        if not email or not password:
            self.set_status("email_password_required")
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
            self.set_status("invalid_credentials")
            return

        app = App.get_running_app()
        self.set_status(None)
        app.open_food_screen(session)

    def open_sign_up(self, instance):
        self.set_status(None)
        self.manager.current = "signup"

    def handle_password_reset(self, instance):
        email = self.email_input.text.strip().lower()

        if not email:
            self.set_status("email_required_for_reset")
            return

        try:
            request_password_reset(email)
        except RequestException:
            self.set_status("reset_request_failed")
            return

        self.set_status("reset_email_sent")
