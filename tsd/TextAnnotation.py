from abc import ABC, abstractmethod
from math import atan2

"""
Note: some annotations make reference to top, bottom, left, and right. However,
all points are assumed to be in 'ij' format (row-major order) to improve
compatability with major image processing libraries (PIL, numpy, OpenCV, etc).
"""


class TextAnnotation(ABC):
    def __init__(self, text):
        self.text = text

    @abstractmethod
    def to_dot(self):
        """
        Returns the annotation as a DotAnnotation. Must be implemented by all 
        subclasses
        """
        pass
    
    @abstractmethod
    def to_box(self):
        """
        Returns the annotation as a BoxAnnotation. Must be implemented by all
        subclasses.
        """
        pass
    
    @abstractmethod
    def to_quad(self):
        """
        Returns the annotation as a QuadAnnotation. Must be implemented by all 
        subclasses.
        """
        pass
    
    @abstractmethod
    def get_data(self):
        """
        Returns the annotation data. Must be implemented by all sublcasses
        """
        pass
    
    # TODO: Handle Polygon 
        
class DotAnnotation(TextAnnotation):
    def __init__(self, text, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 2:
            raise ValueError("Two int values are required")
        self.x, self.y = args
        
    def to_dot(self):
        return self 
    
    def to_box(self):
        """Creates a "box" around the dot"""
        return BoxAnnotation(
            self.text, 
            self.x1-1, self.y1+1, 
            self.x1+1, self.y1-1)
    
    def to_quad(self):
        """
        Creates a "box" around the dot. The order below ensures this quad can
        be drawn as as polygon without overlapping on itself.
        """
        return QuadAnnotation(
            self.text,
            self.x1-1, self.y1+1,
            self.x1-1, self.y1-1,
            self.x1+1, self.y1-1,
            self.x1+1, self.y1+1
        )
        
    def get_data(self):
        return {"x1": self.x1, "y1": self.y1}
    
    def __repr__(self) -> str:
        return f"Box({self.x1}, {self.y1}, {self.text})"
        
class BoxAnnotation(TextAnnotation):
    """
    Standard 2D Box.
    
    Box Annotations should be in the form [left, top, right, bottom]
    """
    def __init__(self, text, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 4:
            raise ValueError("Four int values are required")
        
        # Enforce Boxes to be stored in the same way every time
        points = list(zip(args[::2], args[1::2]))
        
        top_left = min(points, key=lambda p: (p[1], p[0]))
        if points[0] == top_left:
            bottom_right = points[1]
        else:
            bottom_right = points[0]
            
        self.x1, self.y1 = top_left
        self.x2, self.y2 = bottom_right
    
    def to_dot(self):
        """ Returns the centerpoint of the 2D Box """
        x = (self.x1 + self.x2) // 2
        y = (self.y1 + self.y2) // 2
        return DotAnnotation(self.text, x, y)
    
    def to_box(self):
        return self
    
    def to_quad(self):
        """
        Adds the missing two points to make a quad. The order below ensures this
        quad can be drawn as as polygon without overlapping on itself.
        """        
        return QuadAnnotation(
            self.text,
            self.x1, self.y1,
            self.x1, self.y2,
            self.x2, self.y2,
            self.x2, self.y1
        )
    
    def get_data(self):
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2
        }
        
    def __repr__(self):
        return (f"Box([{self.x1}, {self.y1}], "
                    f"[{self.x2}, {self.y2}], {self.text})")
        
class QuadAnnotation(TextAnnotation):
    def __init__(self, text:str, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 8:
            raise ValueError("Eight int values are required")
        
        # Enforce quadrilaterals to be stored in the same order every time        
        points = list(zip(args[::2], args[1::2]))
        
        top_left = min(points, key=lambda p: (p[1], p[0]))
        
        def angle_from_top_left(point):
            dx, dy = point[0] - top_left[0], point[1] - top_left[1]
            return atan2(dy, dx)
        
        points.sort(key=angle_from_top_left)
        self.x1, self.y1 = points[0]
        self.x2, self.y2 = points[1]
        self.x3, self.y3 = points[2]
        self.x4, self.y4 = points[3]
        
        
    def to_dot(self):
        """ 
        Finds the smallest/largest points on both axes and then takes the
        midpoint as an estimate of the centerpoint of the quadrilateral
        """
        
        x = (min([self.x1, self.x2, self.x3, self.x4]) + 
             max([self.x1, self.x2, self.x3, self.x4]) // 2)
        y = (min([self.y1, self.y2, self.y3, self.y4]) + 
             max([self.y1, self.y2, self.y3, self.y4]) // 2)
        return DotAnnotation(self.text, x, y)
    
    def to_box(self):
        left = min([self.x1, self.x2, self.x3, self.x4])
        top = max([self.y1, self.y2, self.y3, self.y4])
        right = max([self.x1, self.x2, self.x3, self.x4])
        bottom = min([self.y1, self.y2, self.y3, self.y4])
        return BoxAnnotation(self.text, left, top, right, bottom)
    
    def to_quad(self):
        return self
        
    def get_data(self):
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "x3": self.x3, "y3": self.y3,
            "x4": self.x4, "y4": self.y4
        }
    
    def __repr__(self):
        return (f"Quad([{self.x1}, {self.y1}], "
                    f"[{self.x2}, {self.y2}], "
                    f"[{self.x3}, {self.y3}], "
                    f"[{self.x4}, {self.y4}], {self.text})")
        
class PolygonAnnotation(TextAnnotation):
    def __init__(self):
        pass