import adsk.fusion

from ...core.geometry.index import Geometry
from ...core.modifier.index import Modifier
from ...core.transform.index import Transform


# @TODO look at this; has both Modifier and Transform
class Array(Modifier):
    def __init__(self, base_geometry: Geometry, count: int, transform: Transform):
        self.base_geometry = base_geometry
        self.count = count
        self.transform = transform

    def apply(self, sketch: adsk.fusion.Sketch):
        for i in range(self.count):
            matrix = self.transform.get_matrix(i, self.count)
            sketch.transform(matrix)
            self.base_geometry.draw(sketch)
            sketch.transform(matrix.inverse())

    def calculate_area(self):
        return self.base_geometry.calculate_area() * self.count
