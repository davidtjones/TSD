from abc import ABC
import math
from shapely.geometry import Polygon
import numpy as np
from queue import Queue
from collections import defaultdict

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
            self.x-1, self.y+1, 
            self.x+1, self.y-1)
            
    def get_data(self):
        return {"x1": self.x, "y1": self.y}
    
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
        
        dx = args[2] - args[0]
        dy = args[3] - args[1]

        if dx < 0 or dy > 0:
            raise ValueError("Box coordinates must be top-left, bottom-right order for screen coordiantes!")
        self.points = list(zip(args[::2], args[1::2]))

        self.x1, self.y1 = self.points[0]
        self.x2, self.y2 = self.points[1]
    
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
        
        self.points = list(zip(args[::2], args[1::2]))

        self.x1, self.y1 = self.points[0]
        self.x2, self.y2 = self.points[1]
        self.x3, self.y3 = self.points[2]
        self.x4, self.y4 = self.points[3]
        
        
    def to_box(self):
        polygon = Polygon(self.points)
        bounding_box = polygon.bounds

        # Shapely uses math coordinates
        minx, miny, maxx, maxy = bounding_box
        bounding_box = [minx, maxy, maxx, miny]
        return BoxAnnotation(self.text, *bounding_box)
    
    def to_polygon(self):
        points = [
            self.x1, self.y1, 
            (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2,
            self.x2, self.y2,
            (self.x2 + self.x3) / 2, (self.y2 + self.y3) / 2,
            self.x3, self.y3,
            (self.x3 + self.x4) / 2, (self.y3 + self.y4) / 2,
            self.x4, self.y4,
            (self.x4 + self.x1) / 2, (self.y4 + self.y1) / 2
        ]
        return PolygonAnnotation(self.text, *points)
        
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

        if len(args) %2 != 0:
            raise ValueError("An even number of values are required!")
        
        self.points = list(zip(args[::2], args[1::2]))
            

    def to_quad(self):
        """
        Quads are actually kind of hard. I'm unsure if it is possible to
        reliably ever convert to a quad because the shape and position are so
        ambiguous. I can ensure that quads are always drawn the same way
        relative to the image axes, but if text is rotated 90 degrees and the
        quad is constructed relative to the angle of the text, there may be a 
        problem. I'd like to test this more and investigate if datasets do this.
        """
        # This may not be a guaranteed solution for very odd shapes.
        poly = Polygon(self.points)

        convex_hull = poly.convex_hull
        
        min_rect = convex_hull.minimum_rotated_rectangle
        ext_coords = list(min_rect.exterior.coords)[:-1] # drop duplicate

        centroid = poly.centroid.coords[0]

        def angle_with_centroid(point):
            return math.atan2(point[1] - centroid[1], point[0] - centroid[0])
        
        # Sort vertices based on angle
        sorted_vertices = sorted(ext_coords, key=angle_with_centroid)

        flattened_points = [int(coord) for point in sorted_vertices for coord in point]

        return QuadAnnotation(self.text, *flattened_points)
    
    def get_data(self):
        out_dict = {}
        for idx, val in enumerate(self.points):
                out_dict[f'x{idx//2 + 1}'], out_dict[f'y{idx//2 + 1}'] = val
        return out_dict
    
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
    
    @staticmethod
    def _bezier_fn(curve, t):
        """Calculate coordinate of a point in the bezier curve"""
        x = (1-t)** 3 * curve[0][0] + 3*(1-t)**2 * t*curve[1][0] + 3*(1-t)*t**2 * curve[2][0] + t**3*curve[3][0]
        y = (1-t)** 3 * curve[0][1] + 3*(1-t)**2 * t*curve[1][1] + 3*(1-t)*t**2 * curve[2][1] + t**3*curve[3][1]
        return x, y
    
    def get_data(self):
        out_dict = {}
        for idx, val in enumerate(self.points):
                out_dict[f'x{idx//2 + 1}'], out_dict[f'y{idx//2 + 1}'] = val
        return out_dict
        
    def to_polygon(self, n=20):
        curve_top = np.array(self.points[:8]).reshape(4, 2)
        curve_bottom = np.array(self.points[8:]).reshape(4, 2)
        
        t = np.linspace(0, 1, n)
        t = t.reshape(-1, 1)
        
        # Setup bezier function
        bernstein = np.array([(1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t**2, t**3])
        bernstein = bernstein.transpose(2, 1, 0)
        
        # Compute points on the curve
        points_top = bernstein @ curve_top
        points_bottom = bernstein @ curve_bottom
        
        polygon_full = np.concatenate(
            (points_top.reshape(-1), 
             points_bottom.reshape(-1)),
            axis=0)
            
        return PolygonAnnotation(self.text, *polygon_full.tolist())
        
    def __repr__(self):
        return (f"Bezier({self.text})")

TextAnnotation.register_conversion(DotAnnotation, BoxAnnotation, DotAnnotation.to_box)
TextAnnotation.register_conversion(BoxAnnotation, DotAnnotation, BoxAnnotation.to_dot)

TextAnnotation.register_conversion(BoxAnnotation, QuadAnnotation, BoxAnnotation.to_quad)
TextAnnotation.register_conversion(QuadAnnotation, BoxAnnotation, QuadAnnotation.to_box)

TextAnnotation.register_conversion(QuadAnnotation, PolygonAnnotation, QuadAnnotation.to_polygon)
TextAnnotation.register_conversion(PolygonAnnotation, QuadAnnotation, PolygonAnnotation.to_quad)

TextAnnotation.register_conversion(BezierCurveAnnotation, PolygonAnnotation, BezierCurveAnnotation.to_polygon)