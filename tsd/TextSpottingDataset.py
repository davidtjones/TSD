from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .TextAnnotation import (TextAnnotation, DotAnnotation, BoxAnnotation, 
                             QuadAnnotation, PolygonAnnotation, 
                             BezierCurveAnnotation)

COLORS = [
    "#ea5545", 
    "#f46a9b", 
    "#ef9b20", 
    "#edbf33", 
    "#ede15b", 
    "#bdcf32", 
    "#87bc45", 
    "#27aeef", 
    "#b33dc6"]

def draw_large_point(draw, x, y, size, fill):
    draw.ellipse([(x - size, y - size), (x + size, y + size)], fill=fill)


class TextSpottingDatasetElement:
    def __init__(self, image_path:str|Path, annotations:list[TextAnnotation]):
        self.image_path = image_path
        self.annotations = annotations
        self.image = None
        self.image_width = None
        self.image_height = None
        
    def _load_image(self):
        self.image = Image.open(self.image_path)
        self.image_width, self.image_height = self.image.size
    
    def __len__(self):
        return len(self.annotations)
    
    def get_data_normalized(self):
        if not self.image_width or self.image_height:
            self._load_image(self)
        normed_annotations = []
        for annotation in self.annotations:
            coords = annotation.get_data()
            normed_data = []
            for key, val in coords.items():
                if key[0] == "x":
                    normed_data.append(val/self.image_width)
                elif key[0] == "y":
                    normed_data.append(val/self.image_height)
            n = type(annotation)(annotation.text, *normed_data)
            normed_annotations.append(n)
        return normed_annotations
    
    def visualize(self, save_path, astype=None):
        if not self.image:
            self._load_image()
        image = self.image.copy()
        
        transparent_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_layer)
        
        font_height = int(self.image_height * .025)
        font = ImageFont.truetype(
            # TODO: maybe just package some font?
            font="UbuntuMono[wght].ttf", 
            size=font_height,
        )
        outline_width = max(int(self.image_height * 0.01), 1)

        for idx, annotation in enumerate(self.annotations):
            color = idx % len(COLORS)
            if astype:
                annotation = annotation.to(astype)
            
            if type(annotation) == BezierCurveAnnotation:
                # Draw the first Bezier curve
                for t in np.arange(0, 1, 0.01):
                    x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[0], t)
                    # draw.point([x, y], COLORS[color])
                    draw_large_point(draw, x, y, outline_width//2, COLORS[color])

                # Draw the second bezier curve
                for t in np.arange(0, 1, 0.01):
                    x, y = BezierCurveAnnotation._bezier_fn(annotation.curves[1], t)
                    # draw.point([x, y], fill=COLORS[color])
                    draw_large_point(draw, x, y, outline_width//2, COLORS[color])

                # Draw the connecting lines
                x1, y1 = annotation.coordinates[0]
                x2, y2 = annotation.coordinates[3]

                x3, y3 = annotation.coordinates[4]
                x4, y4 = annotation.coordinates[7]
                points = [[x1, y1]]

                draw.line([(x1, y1), (x4, y4)], COLORS[color], width=outline_width)
                draw.line([(x2, y2), (x3, y3)], COLORS[color], width=outline_width)
                
            else:
                annotation = annotation.to(QuadAnnotation)
                data = annotation.get_data()
                points = [(data[f'x{i}'], data[f'y{i}']) for i in range(1, len(data)//2 + 1)]
                
                if type(annotation) == DotAnnotation:
                    draw.point(points, fill=COLORS[color])

                else:
                    draw.polygon(
                        points, 
                        outline=COLORS[color],
                        width=outline_width,
                    )

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

class TextSpottingDataset(ABC):
    def __init__(self, root: str|Path, mode:str="train"):
        self.root = Path(root)
        if not self.root.exists():
            raise FileNotFoundError(f"Can't find dataset at {self.root}!!")
        
        self.mode = mode        
        self.image_paths = []
        self.annotations = []
        
    def _setup_mode(self):
        if self.mode.lower() not in ['train', 'test']:
            raise ValueError(f"`mode` must be in [train, test]. "
                             f"Got {self.mode=}")
        
        match self.mode:
            case "train":
                self.images = self.train_images_path
                self.labels = self.train_labels_path
            case "test":
                self.images = self.test_images_path
                self.labels = self.test_labels_path
    
    @abstractmethod
    def _verify_structure(self) -> bool:
        pass
    
    @abstractmethod
    def _build_training(self) -> TextSpottingDatasetElement:
        pass
    
    def build(self):
        if self._verify_structure():
            self._setup_mode()
            self._build_training()


