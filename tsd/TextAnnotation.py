from abc import ABC
from math import atan2
import numpy as np
from queue import Queue
from collections import defaultdict


"""
Note: some annotations make reference to top, bottom, left, and right. However,
all points are assumed to be in 'ij' format (row-major order) to improve
compatability with major image processing libraries (PIL, numpy, OpenCV, etc).
"""

# TESTING: need to test conversions and point-order enforcement

def _enforce_point_order(coordinates:list[int]):
    pairs = list(zip(coordinates[::2], coordinates[1::2]))
        
    top_left = min(pairs, key=lambda p: (p[1], p[0]))
    
    def angle_from_top_left(point):
        dx, dy = point[0] - top_left[0], point[1] - top_left[1]
        return atan2(dy, dx)
    
    pairs.sort(key=angle_from_top_left)
    return pairs

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, source, target):
        self.graph[source].append(target)

    def __getitem__(self, name):
        return self.graph[name]

class TextAnnotation(ABC):
    _conversion_registry = {}
    _conversion_graph = Graph()

    @classmethod
    def register_conversion(cls, source_class, target_class, func):
        cls._conversion_registry[(source_class, target_class)] = func
        cls._conversion_graph.add_edge(source_class, target_class)

    def to(self, target_class):
        conversion_path = self._find_conversion_path(type(self), target_class)
        current_instance = self

        if type(current_instance) != target_class:
            for intermediate_class in conversion_path:
                conversion_func = self._conversion_registry[(type(current_instance), intermediate_class)]
                current_instance = conversion_func(current_instance)
        return current_instance
    
    @classmethod
    def _find_conversion_path(cls, start_class, target_class):
        # use breadth first search to find path from source to target
        q = Queue()
        q.put([start_class])
        while not q.empty():
            curr_path = q.get()
            if curr_path[-1] == target_class:
                return curr_path[1:]
            for e in cls._conversion_graph[curr_path[-1]]:
                q.put(curr_path + [e])

    def __init__(self, text):
        self.text = text
      
class DotAnnotation(TextAnnotation):
    def __init__(self, text, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 2:
            raise ValueError("Two int values are required")
        self.x, self.y = args

    def to_box(self):
        """Creates a "box" around the dot"""
        return BoxAnnotation(
            self.text, 
            self.x1-1, self.y1+1, 
            self.x1+1, self.y1-1)
            
    def get_data(self):
        return {"x1": self.x1, "y1": self.y1}
    
    def __repr__(self) -> str:
        return f"Dot({self.text})"
        
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
        # points = list(zip(args[::2], args[1::2]))
        
        # top_left = min(points, key=lambda p: (p[1], p[0]))
        # if points[0] == top_left:
        #     bottom_right = points[1]
        # else:
        #     bottom_right = points[0]
            
        # self.x1, self.y1 = top_left
        # self.x2, self.y2 = bottom_right

        points = _enforce_point_order(args)
        self.x1, self.y1 = points[0]
        self.x2, self.y2 = points[1]
    
    def to_dot(self):
        """ Returns the centerpoint of the 2D Box """
        x = (self.x1 + self.x2) // 2
        y = (self.y1 + self.y2) // 2
        return DotAnnotation(self.text, x, y)
    
    
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
        return (f"Box({self.text})")
           
class QuadAnnotation(TextAnnotation):
    def __init__(self, text:str, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 8:
            raise ValueError("Eight int values are required")
        
        # Enforce quadrilaterals to be stored in the same order every time        
        # points = list(zip(args[::2], args[1::2]))
        
        # top_left = min(points, key=lambda p: (p[1], p[0]))
        
        # def angle_from_top_left(point):
        #     dx, dy = point[0] - top_left[0], point[1] - top_left[1]
        #     return atan2(dy, dx)
        
        # points.sort(key=angle_from_top_left)
        points = _enforce_point_order(args)

        self.x1, self.y1 = points[0]
        self.x2, self.y2 = points[1]
        self.x3, self.y3 = points[2]
        self.x4, self.y4 = points[3]
        
        
    def to_box(self):
        left = min([self.x1, self.x2, self.x3, self.x4])
        top = max([self.y1, self.y2, self.y3, self.y4])
        right = max([self.x1, self.x2, self.x3, self.x4])
        bottom = min([self.y1, self.y2, self.y3, self.y4])
        return BoxAnnotation(self.text, left, top, right, bottom)
    
    def to_polygon(self):
        points = [
            self.x1, self.y1, 
            (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2,
            self.x2, self.y2,
            (self.x2 + self.x3) / 2, (self.y2 + self.y3) / 2,
            self.x3, self.y3,
            (self.x3 + self.x4) / 2, (self.y3 + self.y4) / 2,
            self.x4, self.y4
            (self.x4 + self.x1) / 2, (self.y4 + self.y1) / 2
        ]
        return PolygonAnnotation(self.text, points)
        
    def get_data(self):
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "x3": self.x3, "y3": self.y3,
            "x4": self.x4, "y4": self.y4
        }
    
    def __repr__(self):
        return (f"Quad({self.text})")
        
class PolygonAnnotation(TextAnnotation):
    def __init__(self, text:str, *args:list[int|float]):
        super().__init__(text=text)
        if len(args) != 16:
            raise ValueError("16 int values are required!")
        
        # Enforce polygon point order to be stored in the same order every time
        points = _enforce_point_order(args)

        self.x1, self.y1 = points[0]
        self.x2, self.y2 = points[1]
        self.x3, self.y3 = points[2]
        self.x4, self.y4 = points[3]
        self.x5, self.y5 = points[4]
        self.x6, self.y6 = points[5]
        self.x7, self.y7 = points[6]
        self.x8, self.y8 = points[7]

    def to_quad(self):
        left = min([self.x1, self.x2, self.x3, self.x4])
        top = max([self.y1, self.y2, self.y3, self.y4])
        right = max([self.x1, self.x2, self.x3, self.x4])
        bottom = min([self.y1, self.y2, self.y3, self.y4])
        return QuadAnnotation(
            self.text,
            [
                left, top,
                left, bottom,
                right, bottom,
                right, top
            ]
        )
    
    def get_data(self):
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "x3": self.x3, "y3": self.y3,
            "x4": self.x4, "y4": self.y4,
            "x5": self.x5, "y5": self.y5,
            "x6": self.x6, "y6": self.y6,
            "x7": self.x7, "y7": self.y7,
            "x8": self.x8, "y8": self.y8
        }

    def __repr__(self):
        return (f"Polygon({self.text})")

class BezierCurveAnnotation(TextAnnotation):
    # Potentially more compact than polygon but can represent more (?) shapes
    def __init__(self, text:str, points:list[list[float]]):
        """
        bezier_data: a 1x16 matrix defining two bezier curves. Each pair of 
        elements defines a coordinate-pair, e.g.
         
        [x1, y1, ... x8, y8, x9, y9, ... x16, y16]
        
        where the first and last pairs of each interior array is an endpoint, 
        and the second and third pairs are control points. The first bezier 
        curve should be located spatially above the second curve.
        """
        super().__init__(text=text)
        if len(points) != 16:
            raise ValueError("16 numerical (int/float) values are required!")
        self.points = points
        self.coordinates = list(zip(self.points[::2], self.points[1::2]))
        self.curves = [self.coordinates[0:4], self.coordinates[4:8]]
        # TODO: shape verification. Check that endpoints at least make sense?
    
    @staticmethod
    def _bezier_fn(curve, t):
        """Calculate coordinate of a point in the bezier curve"""
        x = (1-t)** 3 * curve[0][0] + 3*(1-t)**2 * t*curve[1][0] + 3*(1-t)*t**2 * curve[2][0] + t**3*curve[3][0]
        y = (1-t)** 3 * curve[0][1] + 3*(1-t)**2 * t*curve[1][1] + 3*(1-t)*t**2 * curve[2][1] + t**3*curve[3][1]
        return x, y

    def to_polygon(self):
        u = np.linspace(0, 1, 20)
        bezier = self.bezier.reshape(2, 4, 2).transpose(0, 2, 1).reshape(4, 4)
        points = np.outer((1 - u) ** 3, bezier[:, 0]) \
            + np.outer(3 * u * ((1 - u) ** 2), bezier[:, 1]) \
            + np.outer(3 * (u ** 2) * (1 - u), bezier[:, 2]) \
            + np.outer(u ** 3, bezier[:, 3])
        points = np.concatenate((points[:, :2], points[:, 2:]), axis=0)

        return points

TextAnnotation.register_conversion(DotAnnotation, BoxAnnotation, DotAnnotation.to_box)
TextAnnotation.register_conversion(BoxAnnotation, DotAnnotation, BoxAnnotation.to_dot)

TextAnnotation.register_conversion(BoxAnnotation, QuadAnnotation, BoxAnnotation.to_quad)
TextAnnotation.register_conversion(QuadAnnotation, BoxAnnotation, QuadAnnotation.to_box)

TextAnnotation.register_conversion(QuadAnnotation, PolygonAnnotation, QuadAnnotation.to_polygon)
TextAnnotation.register_conversion(PolygonAnnotation, QuadAnnotation, PolygonAnnotation.to_quad)

TextAnnotation.register_conversion(BezierCurveAnnotation, PolygonAnnotation, BezierCurveAnnotation.to_polygon)