from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from requests import RequestException

from auth_client import sign_up
from translations import translate
from ui_components import RoundedButton


class SignUpScreen(Screen):
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

        self.language_button = RoundedButton(
            text="English",
            font_size=sp(14),
            size_hint=(None, None),
            width=dp(105),
            height=dp(40),
            pos_hint={"right": 0.97, "top": 0.98},
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )
        self.language_button.bind(on_release=self.toggle_language)
        self.add_widget(self.language_button)

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.74, None),
            height=dp(390),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        )

        self.title_label = Label(
            text="Crea account",
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

        self.create_account_button = RoundedButton(
            text="Crea account",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(52),
            my_color=(0.22, 0.68, 0.48, 1),
            color=(1, 1, 1, 1),
        )

        self.login_prompt = Label(
            text="Hai già un account?",
            font_size=sp(14),
            color=(0.02, 0.35, 0.28, 1),
            size_hint_y=None,
            height=dp(26),
        )

        self.sign_in_button = RoundedButton(
            text="Accedi",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(52),
            my_color=(0.10, 0.55, 0.45, 1),
            color=(1, 1, 1, 1),
        )

        self.status_label = Label(
            text="",
            font_size=sp(14),
            color=(0.55, 0.20, 0.20, 1),
            size_hint_y=None,
            height=dp(34),
        )

        self.create_account_button.bind(on_press=self.handle_sign_up)
        self.sign_in_button.bind(on_press=self.open_sign_in)

        form.add_widget(self.title_label)
        form.add_widget(self.email_input)
        form.add_widget(self.password_input)
        form.add_widget(self.create_account_button)
        form.add_widget(self.login_prompt)
        form.add_widget(self.sign_in_button)
        form.add_widget(self.status_label)

        self.add_widget(form)

    def refresh_texts(self, language):
        self.language = language
        self.language_button.text = (
            "Italiano" if language == "en" else "English"
        )
        self.title_label.text = translate(language, "create_account")
        self.create_account_button.text = translate(
            language, "create_account"
        )
        self.login_prompt.text = translate(language, "have_account")
        self.sign_in_button.text = translate(language, "sign_in")

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

    def handle_sign_up(self, instance):
        credentials = self.get_credentials()

        if credentials is None:
            return

        email, password = credentials

        if len(password) < 6:
            self.set_status("password_too_short")
            return

        try:
            result = sign_up(email, password)
        except RequestException:
            self.set_status("signup_failed")
            return

        if result.get("access_token"):
            app = App.get_running_app()
            app.open_food_screen(result)
            return

        self.status_label.color = (0.02, 0.35, 0.28, 1)
        self.set_status("confirm_email")

    def open_sign_in(self, instance):
        self.set_status(None)
        self.manager.current = "auth"
