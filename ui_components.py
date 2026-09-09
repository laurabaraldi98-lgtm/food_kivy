from kivy.graphics import Color, Line, RoundedRectangle
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


class MenuButton(RoundedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.icon_color = Color(1, 1, 1, 1)

            self.top_line = Line(width=dp(2))
            self.middle_line = Line(width=dp(2))
            self.bottom_line = Line(width=dp(2))

        self.update_menu_icon()

    def update_rounded_rect(self, instance, value):
        super().update_rounded_rect(instance, value)

        if hasattr(self, "top_line"):
            self.update_menu_icon()

    def update_menu_icon(self, *args):
        x, y, w, h = self.x, self.y, self.width, self.height

        left = x + w * 0.28
        right = x + w * 0.72
        cy = y + h / 2

        self.top_line.points = (
            left,
            cy + h * 0.16,
            right,
            cy + h * 0.16,
        )

        self.middle_line.points = (
            left,
            cy,
            right,
            cy,
        )

        self.bottom_line.points = (
            left,
            cy - h * 0.16,
            right,
            cy - h * 0.16,
        )
