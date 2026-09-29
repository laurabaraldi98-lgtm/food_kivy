from pathlib import Path

from PIL import Image, ImageDraw


SCALE = 4
CANVAS = 192
OUTPUT = Path("images")
OUTPUT.mkdir(exist_ok=True)


def blank_canvas():
    return Image.new(
        "RGBA",
        (CANVAS * SCALE, CANVAS * SCALE),
        (0, 0, 0, 0),
    )


def save_icon(image, filename):
    image = image.resize(
        (CANVAS, CANVAS),
        Image.Resampling.LANCZOS,
    )
    image.save(OUTPUT / filename)


def draw_italian_flag():
    image = blank_canvas()
    draw = ImageDraw.Draw(image)

    left = 24 * SCALE
    top = 48 * SCALE
    stripe = 48 * SCALE
    height = 96 * SCALE

    draw.rectangle(
        (left, top, left + stripe - 1, top + height - 1),
        fill="#009246",
    )
    draw.rectangle(
        (left + stripe, top, left + 2 * stripe - 1, top + height - 1),
        fill="#FFFFFF",
    )
    draw.rectangle(
        (left + 2 * stripe, top, left + 3 * stripe - 1, top + height - 1),
        fill="#CE2B37",
    )

    save_icon(image, "flag_it.png")


def draw_british_flag():
    image = blank_canvas()

    left = 16 * SCALE
    top = 48 * SCALE
    width = 160 * SCALE
    height = 96 * SCALE

    blue = (1, 33, 105, 255)
    white = (255, 255, 255, 255)
    red = (200, 16, 46, 255)

    for y in range(height):
        v = y * 30 / height

        for x in range(width):
            u = x * 50 / width
            color = blue

            descending = v - 0.6 * u
            ascending = v - (30 - 0.6 * u)

            if abs(descending) <= 3 or abs(ascending) <= 3:
                color = white

            if (
                (u < 25 and 0 <= descending <= 2)
                or (u >= 25 and -2 <= descending <= 0)
                or (u < 25 and -2 <= ascending <= 0)
                or (u >= 25 and 0 <= ascending <= 2)
            ):
                color = red

            if abs(u - 25) <= 5 or abs(v - 15) <= 5:
                color = white

            if abs(u - 25) <= 3 or abs(v - 15) <= 3:
                color = red

            image.putpixel((left + x, top + y), color)

    save_icon(image, "flag_en.png")


draw_italian_flag()
draw_british_flag()
print("Create images/flag_it.png e images/flag_en.png")
