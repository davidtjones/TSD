import unittest
from textmark import TextAnnotation


class GetDataTest(unittest.TestCase):
    """
    This test case was written to ensure that the inherited get_data correctly
    provides the data for each class. Of particular note is that the first values
    are actually popped from the data dictionary, and then we test points with
    `list(data.values())` to ensure that whatever is remaining is nothing but
    the point data, and that it matches the original points array in every case
    Passing this test case should ensure that our serialization is consistent
    and reliable.
    """

    def test_dot(self):
        points = [25, 100]
        my_dot = TextAnnotation.factory("Dot", "dot-test", "english", *points)
        data = my_dot.get_data()
        _type = data.pop("type")
        text = data.pop("text")
        lang = data.pop("language")
        self.assertEqual(_type, "Dot")
        self.assertEqual(text, "dot-test")
        self.assertEqual(lang, "english")
        self.assertEqual(points, list(data.values()))

    def test_box(self):
        # Boxes must be upper-left bottom-right in screen format
        points = [25, 100, 50, 1010]
        my_box = TextAnnotation.factory("Box", "box-test", "english", *points)
        data = my_box.get_data()
        _type = data.pop("type")
        text = data.pop("text")
        lang = data.pop("language")
        self.assertEqual(_type, "Box")
        self.assertEqual(text, "box-test")
        self.assertEqual(lang, "english")
        self.assertEqual(points, list(data.values()))

    def test_quad(self):
        points = [25, 100, 50, 100, 50, 1010, 25, 1010]
        my_quad = TextAnnotation.factory("Quad", "quad-test", "english", *points)

        data = my_quad.get_data()
        _type = data.pop("type")
        text = data.pop("text")
        lang = data.pop("language")
        self.assertEqual(_type, "Quad")
        self.assertEqual(text, "quad-test")
        self.assertEqual(lang, "english")
        self.assertEqual(points, list(data.values()))

    def test_poly(self):
        # I just filled in some points here
        points = [25, 100, 37.5, 100, 50, 100, 50, 555, 50, 1010, 37.5, 1010, 25, 1010]
        my_quad = TextAnnotation.factory("Poly", "poly-test", "english", *points)

        data = my_quad.get_data()
        _type = data.pop("type")
        text = data.pop("text")
        lang = data.pop("language")
        self.assertEqual(_type, "Poly")
        self.assertEqual(text, "poly-test")
        self.assertEqual(lang, "english")
        self.assertEqual(points, list(data.values()))

    def test_bezier(self):
        # These points came from the example data.json
        points = [
            305,
            433,
            383.37,
            458.8,
            404.23,
            439.96,
            464,
            423,
            460,
            462,
            405.58,
            474.53,
            380.33,
            489.72,
            305,
            462,
        ]
        my_quad = TextAnnotation.factory("Bezier", "bezier-test", "english", *points)

        data = my_quad.get_data()
        _type = data.pop("type")
        text = data.pop("text")
        lang = data.pop("language")
        self.assertEqual(_type, "Bezier")
        self.assertEqual(text, "bezier-test")
        self.assertEqual(lang, "english")
        self.assertEqual(points, list(data.values()))


if __name__ == "__main__":
    unittest.main()
