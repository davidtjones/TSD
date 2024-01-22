import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .TextAnnotation import (
    BezierCurveAnnotation,
    BoxAnnotation,
    DotAnnotation,
    QuadAnnotation,
)
from .tools import FontHandler

supported_latin_langs = ["english", "latin", "french", "german", "spanish"]
supported_asian_langs = ["chinese", "japanese", "korean"]
supported_meast_langs = ["arabic"]


def draw_large_point(draw, x, y, size, fill):
    draw.ellipse([(x - size, y - size), (x + size, y + size)], fill=fill)


def draw_numbered_point(draw, x, y, size, num: str, font, font_height):
    draw.ellipse([(x - size, y - size), (x + size, y + size)], fill="#000000")
    text_width = draw.textlength(str(num), font=font)
    draw.text(
        (x - text_width / 2, y - font_height / 2),
        num,
        font=font,
        fill="white",
        stroke_fill="black",
    )


class Visualizer:
    def __init__(self, image_path, annotations, colors=None):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.image_width, self.image_height = self.image.size
        self.annotations = annotations

        self.colors = colors
        if not self.colors:
            self.colors = [
                "#ea5545",
                "#f46a9b",
                "#ef9b20",
                "#edbf33",
                "#ede15b",
                "#bdcf32",
                "#87bc45",
                "#27aeef",
                "#b33dc6",
            ]

        self.font_handler = FontHandler()

    def visualize(self, astype=None, save_path=None, draw_vertex_numbers=False):
        vis_image = self.image.copy()
        transparent_layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_layer)

        outline_width = max(int(self.image_height * 0.01), 1)
        font_height = int(self.image_height * 0.03)

        lang_name_font = ImageFont.truetype(
            font=self.font_handler.get_font("NotoSans"),
            size=font_height,
        )

        for idx, annotation in enumerate(self.annotations):
            color = idx % len(self.colors)
            if astype:
                annotation = annotation.to(astype)

            # Draw the shape of the annotation
            if type(annotation) == BezierCurveAnnotation:
                # None of this is needed since we can just convert to polygon!!
                # However it is useful for testing.

                # Draw the first Bezier curve
                for t in np.arange(0, 1, 0.01):
                    x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[0], t)
                    draw_large_point(draw, x, y, outline_width // 2, self.colors[color])

                # Draw the second bezier curve
                for t in np.arange(0, 1, 0.01):
                    x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[1], t)
                    draw_large_point(draw, x, y, outline_width // 2, self.colors[color])

                # Draw the connecting lines
                x1, y1 = annotation.coordinates[0]
                x2, y2 = annotation.coordinates[3]

                x3, y3 = annotation.coordinates[4]
                x4, y4 = annotation.coordinates[7]

                # This list informs where to put the text label
                points = [[x1, y1]]

                if draw_vertex_numbers:
                    draw_numbered_point(
                        draw,
                        x1,
                        y1 - font_height,
                        outline_width * 1.5,
                        "1",
                        lang_name_font,
                        font_height,
                    )
                    draw_numbered_point(
                        draw,
                        x2,
                        y2 - font_height,
                        outline_width * 1.5,
                        "2",
                        lang_name_font,
                        font_height,
                    )
                    draw_numbered_point(
                        draw,
                        x3,
                        y3 - font_height,
                        outline_width * 1.5,
                        "3",
                        lang_name_font,
                        font_height,
                    )
                    draw_numbered_point(
                        draw,
                        x4,
                        y4 - font_height,
                        outline_width * 1.5,
                        "4",
                        lang_name_font,
                        font_height,
                    )

                draw.line([(x1, y1), (x4, y4)], self.colors[color], width=outline_width)
                draw.line([(x2, y2), (x3, y3)], self.colors[color], width=outline_width)

            else:
                if type(annotation) == BoxAnnotation:
                    # We only need to do this so we can plot boxes with draw.polygon
                    annotation = annotation.to(QuadAnnotation)

                data = annotation.get_data()
                points = [
                    (data[f"x{i}"], data[f"y{i}"]) for i in range(1, len(data) // 2 + 1)
                ]

                if type(annotation) == DotAnnotation:
                    draw_large_point(
                        draw,
                        points[0][0],
                        points[0][1],
                        outline_width,
                        self.colors[color],
                    )

                else:
                    draw.polygon(
                        points,
                        outline=self.colors[color],
                        width=outline_width,
                    )

                    if draw_vertex_numbers:
                        # high res polygons may come out a little busy
                        for idx, (x, y) in enumerate(points):
                            draw_numbered_point(
                                draw,
                                x,
                                y,
                                outline_width * 1.5,
                                str(idx + 1),
                                lang_name_font,
                                font_height,
                            )

            # Handle font and text drawing
            atext = annotation.text
            alang = annotation.language.lower()

            # We need english font every time to display the language name

            match alang:
                case (
                    "latin"
                    | "english"
                    | "german"
                    | "french"
                    | "spanish"
                    | "italian"
                    | "none"
                    | "symbols"
                    | None
                ):
                    lang_font_path = self.font_handler.get_font("NotoSans")
                case "chinese":
                    lang_font_path = self.font_handler.get_font("NotoSansSC")
                case "japanese":
                    lang_font_path = self.font_handler.get_font("NotoSansJP")
                case "korean":
                    lang_font_path = self.font_handler.get_font("NotoSansKR")
                case "bengali" | "bangla":
                    lang_font_path = self.font_handler.get_font("NotoSansBengali")
                case "devanagari" | "hindi":
                    lang_font_path = self.font_handler.get_font("NotoSansDevanagari")
                case "arabic":
                    lang_font_path = self.font_handler.get_font("NotoSansArarbic")
                case _:
                    raise ValueError(
                        f'Unsupported language "{alang}" for text: {atext}. See image {self.image_path}'
                    )

            lang_font = ImageFont.truetype(font=lang_font_path, size=font_height)

            x_text = points[0][0]
            y_text = points[0][1] - font_height

            alang = f" [{alang.capitalize()}]"

            lang_name_width = draw.textlength(alang, font=lang_name_font)
            lang_text_width = draw.textlength(atext, font=lang_font)
            draw.rectangle(
                [
                    x_text,
                    y_text,
                    x_text + lang_text_width + lang_name_width,
                    y_text + font_height,
                ],
                fill=self.colors[color],
            )

            draw.text(
                (x_text, y_text),
                atext,
                font=lang_font,
                fill="white",
                stroke_fill="black",
            )

            draw.text(
                (x_text + lang_text_width, y_text),
                alang,
                font=lang_name_font,
                fill="white",
                stroke_fill="black",
            )

        vis_image.paste(transparent_layer, mask=transparent_layer)
        if save_path:
            vis_image.save(save_path)
        return vis_image
