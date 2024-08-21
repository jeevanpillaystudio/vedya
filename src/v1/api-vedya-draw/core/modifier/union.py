import adsk.fusion

from ..geometry.index import Geometry
from .index import Modifier


class Union(Modifier):
    def __init__(self, *geometries):
        self.geometries = geometries

    def apply(self, sketch: adsk.fusion.Sketch):
        for geometry in self.geometries:
            geometry.draw(sketch)

    def calculate_area(self):
        # Simplified area calculation
        return sum(geometry.calculate_area() for geometry in self.geometries)
