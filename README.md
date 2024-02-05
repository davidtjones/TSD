# Text Annotation Utilities
This project supports buildling datasets for downstream tasks using many
open-source text-spotting datasets. It includes a number of classes and tools to
quickly and easily build text spotting datasets with many annotation types, 
including

* Dot
* 2-point bounding boxes
* Quadrilateral bounding boxes
* Polygons
* Bezier Curves

Additionally, this library makes converting between types extremely easy through an intuitive and extensible interface.

![example](./example/example.gif)

## Setup
Use pip to install: 
```
pip install textmark
```

## TextAnnotation
`TextAnnotation` is a base class that can be easily extended to support other annotation formats. This library includes several formats already. Of particular note is that TextAnnotation includes a class level conversion registry. Subclasses can be registered like so:

```python
# Add your subclass name:
TextAnnotation.register_name(name, "My_Class")
```

```python
# Add any relevant conversions
# you only need to convert to the "closest" next annotation type
TextAnnotation.register_conversion(BoxAnnotation, QuadAnnotation, BoxAnnotation.to_quad)
TextAnnotation.register_conversion(QuadAnnotation, BoxAnnotation, QuadAnnotation.to_box)
```

Now, a user can easily convert between Box and Quad annotations through the use of 
```python
my_quad_annotation.to("Box")
```

If there are additional registries, such as Quad <--> Polygon, the user can convert all the way from a Box to a Polygon annotation (or vice versa) in a single command:
```python
my_polygon_annotation.to("Box")
```

This system works by constructing a graph of all registered conversions. When a user calls the `.to` method, the graph is searched for the target class, and then applies all conversions on that path. This library implements the following simple conversions, which can be automatically chained together:

Polygon <--> Quad \
Quad <--> Box \
Box <--> Dot

Note that moving up through the chain is a lossy process!!

In addition, Bezier Curves can be converted to Polygons.

## Visualizing
This library also includes an easy visualization system. See the example below:
```python
from textmark import TextAnnotation, Visualizer

img_path = ...

my_annotation = TextAnnotation.factory(
    "Poly", scene_text, language, *list_of_points
)

my_second_annotation = TextAnnotation.factory(
    ...
)

# Can visualize an arbitrary number of annotations
vis = Visualizer(img_path, [my_annotation, my_second_annotation, ...])
visualization = vis.visualize()
visualize.show()  # uses PIL
```

