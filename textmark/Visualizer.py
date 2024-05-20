import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .TextAnnotation import (
    BezierCurveAnnotation,
    BoxAnnotation,
    DotAnnotation,
    QuadAnnotation,
)
from .tools import FontHandler


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
    def __init__(self, annotations, image_path=None, image=None, colors=None):
        self.image_path = image_path
        self.image = image
        if image_path and image:
            raise ValueError("Provide only one of image_path and image")
        
        if image_path:
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

    def visualize(
        self,
        save_path=None,
        draw_language_name=False,
        draw_vertex_numbers=False,
        draw_annotation_order=False,
        outline_width="auto",
        font_height="auto"
    ):
        """
        Visualize the image.

        astype: Provide an annotation type (e.g., BoxAnnotation) to visualize
            the annotation as that type.

        save_path: provide a path here to save the image out

        draw_vertex_numbers if useful to verify that your representation is
            expected.
        """
        vis_image = self.image.copy()
        transparent_layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_layer)

        if outline_width == "auto":
            outline_width = max(int(self.image_height * 0.01), 1)
        else:
            if not isinstance(outline_width, int):
                raise ValueError("outline_width must be an integer")

        if font_height == "auto":
            font_height = int(self.image_height * 0.03)
        else:
            if not isinstance(font_height, int):
                raise ValueError("font_height must be an integer")

        lang_name_font = ImageFont.truetype(
            font=self.font_handler.get_font("NotoSans"),
            size=font_height,
        )

        for idx, annotation in enumerate(self.annotations):
            color = idx % len(self.colors)

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
                x1, y1 = annotation.points[0]
                x2, y2 = annotation.points[3]

                x3, y3 = annotation.points[4]
                x4, y4 = annotation.points[7]

                # This list informs where to put the text label
                points = [[x1, y1]]

                if draw_vertex_numbers:
                    d = zip(
                        ["1", "2", "3", "4"], [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                    )
                    for num, (xx, yy) in d:
                        draw_numbered_point(
                            draw,
                            xx,
                            yy - font_height,
                            outline_width * 1.5,
                            num,
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
                    (data[f"x{i}"], data[f"y{i}"])
                    for i in range(1, (len(data) - 3) // 2 + 1)
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

            if draw_annotation_order:
                atext += f" [{str(idx)}]"

            x_text = points[0][0]
            y_text = points[0][1] - font_height

            # We need english font every time to display the language name
            alang = annotation.language.lower()

            if alang in ["latin", "english", "german", "french", "spanish", "italian", "none", "symbols", None]:
                lang_font_path = self.font_handler.get_font("NotoSans")
            elif alang == "chinese":
                lang_font_path = self.font_handler.get_font("NotoSansSC")
            elif alang == "japanese":
                lang_font_path = self.font_handler.get_font("NotoSansJP")
            elif alang == "korean":
                lang_font_path = self.font_handler.get_font("NotoSansKR")
            elif alang in ["bengali", "bangla"]:
                lang_font_path = self.font_handler.get_font("NotoSansBengali")
            elif alang in ["devanagari", "hindi"]:
                lang_font_path = self.font_handler.get_font("NotoSansDevanagari")
            elif alang == "arabic":
                lang_font_path = self.font_handler.get_font("NotoSansArabic")  # Fixed typo from "Ararbic" to "Arabic"
            else:
                raise ValueError(f'Unsupported language "{alang}" for text: {atext}. See image {self.image_path}')

            lang_font = ImageFont.truetype(font=lang_font_path, size=font_height)
            alang = f" [{alang.capitalize()}]"
            lang_text_width = draw.textlength(atext, font=lang_font)

            lang_name_width = (
                draw.textlength(alang, font=lang_name_font) if draw_language_name else 0
            )
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
            if draw_language_name:
                draw.text(
                    (x_text + lang_text_width, y_text),
                    alang,
                    font=lang_name_font,
                    fill="white",
                    stroke_fill="black",
                )

        vis_image.paste(transparent_layer, mask=transparent_layer)
        if save_path:
            if vis_image.mode != "RGB":
                vis_image.convert("RGB")
            vis_image.save(save_path)
        return vis_image
