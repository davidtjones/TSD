import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .TextAnnotation import (
    BezierCurveAnnotation,
    BoxAnnotation,
    DotAnnotation,
    QuadAnnotation,
)

COLORS = [
    "#ea5545", "#f46a9b", "#ef9b20", 
    "#edbf33", "#ede15b", "#bdcf32", 
    "#87bc45", "#27aeef", "#b33dc6" ]

def draw_large_point(draw, x, y, size, fill):
    draw.ellipse([(x - size, y - size), (x + size, y + size)], fill=fill)

def draw_numbered_point(draw, x, y, size, num:str, font, font_height):
    draw.ellipse([(x - size, y - size), (x + size, y + size)], fill='#000000')
    text_width = draw.textlength(str(num), font=font)
    draw.text((x-text_width/2, y-font_height/2), num, font=font, fill='white', stroke_fill='black')


def visualize(tsde, save_path, astype=None, draw_vertex_numbers=False):
    if not tsde.image:
        tsde._load_image()
    image = tsde.image.copy()
    
    transparent_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(transparent_layer)
    
    font_height = int(tsde.image_height * .025)
    font = ImageFont.truetype(
        # TODO: maybe just package some font?
        font="UbuntuMono[wght].ttf", 
        size=font_height,
    )
    outline_width = max(int(tsde.image_height * 0.01), 1)

    for idx, annotation in enumerate(tsde.annotations):
        color = idx % len(COLORS)
        if astype:
            annotation = annotation.to(astype)
        
        if type(annotation) == BezierCurveAnnotation:
            # None of this is needed since we can just convert to polygon!!
            # However it is useful for testing.
            
            # Draw the first Bezier curve
            for t in np.arange(0, 1, 0.01):
                x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[0], t)
                draw_large_point(draw, x, y, outline_width//2, COLORS[color])

            # Draw the second bezier curve
            for t in np.arange(0, 1, 0.01):
                x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[1], t)
                draw_large_point(draw, x, y, outline_width//2, COLORS[color])

            # Draw the connecting lines
            x1, y1 = annotation.coordinates[0]
            x2, y2 = annotation.coordinates[3]

            x3, y3 = annotation.coordinates[4]
            x4, y4 = annotation.coordinates[7]
            
            # This list informs where to put the text label
            points = [[x1, y1]]

            if draw_vertex_numbers:
                draw_numbered_point(draw, x1, y1-font_height, outline_width*1.5, "1", font, font_height)
                draw_numbered_point(draw, x2, y2-font_height, outline_width*1.5, "2", font, font_height)
                draw_numbered_point(draw, x3, y3-font_height, outline_width*1.5, "3", font, font_height)
                draw_numbered_point(draw, x4, y4-font_height, outline_width*1.5, "4", font, font_height)

            draw.line([(x1, y1), (x4, y4)], COLORS[color], width=outline_width)
            draw.line([(x2, y2), (x3, y3)], COLORS[color], width=outline_width)
            
        else:
            if type(annotation) == BoxAnnotation:
                # We only need to do this so we can plot boxes with draw.polygon
                annotation = annotation.to(QuadAnnotation)

            data = annotation.get_data()
            points = [(data[f'x{i}'], data[f'y{i}']) for i in range(1, len(data)//2 + 1)]
            
            if type(annotation) == DotAnnotation:
                draw_large_point(draw, points[0][0], points[0][1], outline_width, COLORS[color])

            else:
                draw.polygon(
                    points, 
                    outline=COLORS[color],
                    width=outline_width,
                )

                if draw_vertex_numbers:
                    for idx, (x, y) in enumerate(points):
                        draw_numbered_point(draw, x, y, outline_width*1.5, str(idx+1), font, font_height)

        x_text = points[0][0]
        y_text = points[0][1] - font_height

        text_width  = draw.textlength(annotation.text, font=font)
        draw.rectangle([x_text, y_text, x_text + text_width, y_text + font_height], fill=COLORS[color])
        
        draw.text(
            (x_text, y_text),
            annotation.text, 
            font=font,
            fill='white',
            stroke_fill='black')
        
        idx += 1
        if idx == len(COLORS):
            idx = 0
    
    image.paste(transparent_layer, mask=transparent_layer)
    image.save(save_path)