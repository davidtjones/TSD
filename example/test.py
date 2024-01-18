import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tau import (
    BezierCurveAnnotation, BoxAnnotation, DotAnnotation, PolygonAnnotation, 
    QuadAnnotation)

from tau import Visualizer

def create_gif(image_folder, output_path, duration):
    images = []
    folder_path = Path(image_folder)

    font_size = 40
    font = ImageFont.truetype(
        # TODO: maybe just package some font?
        "UbuntuMono[wght].ttf", 
        font_size
    )

    # Collecting image files
    for file_path in sorted(folder_path.glob('*.png')):
        image = Image.open(file_path)

        # Drawing the filename on the image
        draw = ImageDraw.Draw(image)
        text = file_path.stem  # or str(file_path) for full path
        text_width = draw.textlength(text, font=font)
        text_position = (250-text_width//2, 200)  # Change the position as needed

        draw.text(text_position, text, font=font, fill=(255, 255, 255), stroke_fill='black')  # White text
        
        images.append(image)

    # Convert duration from seconds to milliseconds
    duration_ms = int(duration * 1000)

    # Saving as GIF
    images[0].save(output_path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0)

out_path = Path("out")
out_path.mkdir(parents=True, exist_ok=True)

# Build annotations
with open("data.json", 'r') as fp:
    data = json.load(fp)

annotations = []
for ant in data:
    text = ant['rec']
    my_ant = BezierCurveAnnotation(text, ant['bezier_pts'])
    annotations.append(my_ant)


image_path = "data.png"

# Test converting annotations
# Bez -> Poly, Bez -> Quad, Bez -> Box, Bez -> Dot (tree walk)
for conv, name in zip(
    [BezierCurveAnnotation, PolygonAnnotation, QuadAnnotation, BoxAnnotation, DotAnnotation],
    ['bezier', 'polygon', 'quad', 'box', 'dot']):
    vis = Visualizer(image_path, annotations)
    vis.visualize(astype=conv, save_path=out_path / f"{name}.png")    
        


create_gif(out_path, "example.gif", 2)