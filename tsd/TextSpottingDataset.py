from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from TextAnnotation import TextAnnotation, BoxAnnotation, DotAnnotation, QuadAnnotation

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
    
    def visualize(self, save_path):
        if not self.image:
            self._load_image()
        image = self.image.copy()
        transparent_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_layer)
        font_height = int(self.image_height * .025)
        outline_width = max(int(self.image_height * 0.01), 1)
        font = ImageFont.truetype(
            # TODO: maybe just package some font?
            font="Arial.TTF", 
            size=font_height,
        )
        
        for idx, annotation in enumerate(self.annotations):
            data = annotation.to_quad().get_data()
            points = [(data[f'x{i}'], data[f'y{i}']) for i in range(1, len(data)//2 + 1)]
            
            x_text = points[0][0]
            y_text = points[0][1] - font_height
            
            if type(annotation) != DotAnnotation:
                draw.polygon(
                    points, 
                    outline=COLORS[idx],
                    width=outline_width,
                )
                
            else:
                draw.point(points, COLORS[idx])
            
            text_width, text_height = draw.textsize(annotation.text, font=font)
            draw.rectangle([x_text, y_text, x_text + text_width, y_text + text_height], fill=COLORS[idx])
            
            draw.text(
                (x_text, y_text),
                annotation.text, 
                font=font,
                fill='white',
                stroke_fill='black')
        
        image.paste(transparent_layer, mask=transparent_layer)
        image.save(save_path)

class TextSpottingDataset(ABC):
    def __init__(self, root: str|Path, mode:str="train"):
        self.root = Path(root)
        if not self.root.exists():
            raise FileNotFoundError(f"Can't find dataset at {self.root}!!")
        
        self.mode = mode
        if self.mode.lower() not in ['train', 'test']:
            raise ValueError(f"`mode` must be in [train, test]. Got {mode=}")
        
        self.image_paths = []
        self.annotations = []
        
    def _setup_mode(self):
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


class ICDAR2013(TextSpottingDataset):
    # Scene text dataset containing most of the well-captured and horizontal
    # texts, annotated in boundng box formats.
    # [Source](https://iapr.org/archives/icdar2013/). 
    # Also see: https://rrc.cvc.uab.es/?ch=2&com=downloads
    # 1. 229 training images
    # 2. 233 test images
    def __init__(self, root: str|Path, mode: str="train"):
        super().__init__(root, mode)
        self.name = "ICDAR2013"
        self.train_images_path = self.root / "Challenge2_Training_Task12_Images"
        self.train_labels_path = self.root / "Challenge2_Training_Task1_GT"
        
        self.test_images_path = self.root / "Challenge2_Test_Task12_Images"
        self.test_labels = self.root / "Challenge2_Test_Task1_GT"

    def _verify_structure(self):
        for d in [self.train_images_path, self.train_labels_path, 
                  self.test_images_path, self.test_labels]:
            if not d.exists():
                raise FileNotFoundError(f"Couldn't find {d.resolve()} for "
                                        f"{self.name}, check folder structure.")
        return True
    
    def _build_training(self):
        image_paths = []
        annotations = []
        for train_img_path in self.images.glob("*.jpg"):
            anno = []
            gt_fname = ("gt_"+train_img_path.stem+".txt")
            train_label_path = self.labels / gt_fname
            
            with open(train_label_path, 'r') as f:
                for line in f.readlines():
                    left, top, right, bottom, text = line.strip().split(" ")
                    anno.append(
                        BoxAnnotation(text.replace("\"", ""), 
                                      int(left), 
                                      int(top), 
                                      int(right), 
                                      int(bottom)))
            image_paths.append(train_img_path)
            annotations.append(anno)
        
        self.image_paths = image_paths
        self.annotations = annotations

    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> tuple[str, list[TextAnnotation]]:
        return TextSpottingDatasetElement(
            self.image_paths[idx], 
            self.annotations[idx])

class ICDAR2015(ICDAR2013):
    # A scene text dataset containing inclined texts. Annotated using
    # quadrilateral format. [Source](https://rrc.cvc.uab.es/?ch=4).
    # Also see: https://rrc.cvc.uab.es/?ch=2&com=downloads
    # 1. 1000 training images
    # 2. 500 test images
    def __init__(self, root: str|Path, mode: str="train"):
        super().__init__(root, mode)
        self.name = "ICDAR2015"
        self.train_images_path = self.root / "ch4_training_images"
        self.train_labels_path = self.root / "ch4_training_localization_transcription_gt"
        
        self.test_images_path = self.root / "ch4_test_images"
        self.test_labels = self.root / "Challenge4_Test_Task1_GT"
        
    def _build_training(self):
        image_paths = []
        annotations = []
        for train_img_path in self.images.glob("*.jpg"):
            anno = []
            gt_fname = ("gt_"+train_img_path.stem+".txt")
            train_label_path = self.labels / gt_fname
            
            with open(train_label_path, 'r') as f:
                for line in f.readlines():
                    line_data = line.strip().split(",")
                    x1, y1, x2, y2, x3, y3, x4, y4 = line_data[:8]
                    
                    # Sometimes there is a commma at the end of the word 
                    text = "".join(line_data[8:])
                    anno.append(
                        QuadAnnotation(
                            text, 
                            int(x1), int(y1), 
                            int(x2), int(y2), 
                            int(x3), int(y3), 
                            int(x4), int(y4)))
            image_paths.append(train_img_path)
            annotations.append(anno)
        
        self.image_paths = image_paths
        self.annotations = annotations
        

if __name__ == "__main__":
    import code
    d = ICDAR2013("../sources/icdar2013")
    d.build()
    d[0].visualize('test.png')
        
    code.interact(local=locals())