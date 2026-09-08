from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button


class RoundedButton(Button):
    def __init__(
        self,
        my_color=(0.10, 0.55, 0.45, 1),
        **kwargs
    ):
        super().__init__(**kwargs)

        self.my_color = my_color
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)

        with self.canvas.before:
            self.button_color = Color(*self.my_color)

            self.rounded_rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(18)]
            )

        self.bind(
            pos=self.update_rounded_rect,
            size=self.update_rounded_rect
        )

    def update_rounded_rect(self, instance, value):
        self.rounded_rect.pos = self.pos
        self.rounded_rect.size = self.size
