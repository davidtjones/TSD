from abc import ABC, abstractmethod
from pathlib import Path
from .TextAnnotation import TextAnnotation
from PIL import Image
    

class TSElement:
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
    
    def __getitem__(self, idx):
        return self.annotations[idx]
    
    def __setitem__(self, idx, item:TextAnnotation):
        if type(item) != TextAnnotation:
            return TypeError("Can only set to Text Annotations")
        self.annotations[idx] = item
    
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
    
class TSDataset(ABC):
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
    def _build_training(self) -> TSElement:
        pass
    
    def build(self):
        if self._verify_structure():
            self._setup_mode()
            self._build_training()


