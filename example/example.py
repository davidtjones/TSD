import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.append("../textmark")
from textmark import TextAnnotation, Visualizer
from textmark.tools import FontHandler


def create_gif(image_folder, output_path, duration):
    images = []
    folder_path = Path(image_folder)
    font_handler = FontHandler()
    font_size = 40

    font = ImageFont.truetype(font_handler.get_font("NotoSans"), font_size)

    # Collecting image files
    for file_path in sorted(folder_path.glob("*.png")):
        image = Image.open(file_path)

        # Drawing the filename on the image
        draw = ImageDraw.Draw(image)
        text = file_path.stem  # or str(file_path) for full path
        text_width = draw.textlength(text, font=font)
        text_position = (250 - text_width // 2, 200) 

        draw.text(
            text_position, text, font=font, fill=(255, 255, 255), stroke_fill="black"
        )

        images.append(image)

    duration_ms = int(duration * 1000)

    # Saving as GIF
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
    )

out_path = Path("example/out")
out_path.mkdir(parents=True, exist_ok=True)

# Build annotations
with open("example/data.json", "r") as fp:
    data = json.load(fp)

annotations = [
    TextAnnotation.factory("Bezier", ant['rec'], "English", *ant['bezier_pts'])
    for ant in data
]

image_path = "example/data.png"

# Test converting annotations
# Bez -> Bez, Bez -> Poly, Bez -> Quad, Bez -> Box, Bez -> Dot
for annotation_type in ("Bezier", "Poly", "Quad", "Box", "Dot"):
    converted_anntations = [ant.to(annotation_type) for ant in annotations]

    vis = Visualizer(converted_anntations, image_path=image_path)
    vis.visualize(
        save_path=out_path / f"{annotation_type}.png",
        draw_language_name=False,
        draw_vertex_numbers=False,
    )

create_gif(out_path, "example/example.gif", 2)
