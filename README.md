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
This package isn't on PyPI (yet), but you can still use pip to install it: 
```
pip install git+https://github.com/davidtjones/TSD.git
```

## TextAnnotation
`TextAnnotation` is a base class that can be easily extended to support other annotation formats. This library includes several formats already. Of particular note is that TextAnnotation includes a class level conversion registry. Subclasses can be registered like so:
```
TextAnnotation.register_conversion(BoxAnnotation, QuadAnnotation, BoxAnnotation.to_quad)
TextAnnotation.register_conversion(QuadAnnotation, BoxAnnotation, QuadAnnotation.to_box)
```

Now, a user can easily convert between Box and Quad annotations through the use of 
```
my_quad_annotation.to(BoxAnnotation)
```

If there are additional registries, such as Quad <--> Polygon, the user can convert all the way from a Box to a Polygon annotation (or vice versa) in a single command:
```
my_polygon_annotation.to(BoxAnnotation)
```

This system works by constructing a graph of all registered conversions. When a user calls the `.to` method, the graph is searched for the target class, and then applies all conversions on that path. This library implements the following simple conversions, which can be automatically chained together:

Polygon <--> Quad \
Quad <--> Box \
Box <--> Dot

Note that moving up through the chain is a lossy process!!

In addition, Bezier Curves can be converted to Polygons.
