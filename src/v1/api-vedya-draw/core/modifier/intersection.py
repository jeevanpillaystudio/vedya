import adsk.fusion

from ..geometry.index import Geometry
from .index import Modifier


class Intersection(Modifier):
    def __init__(self, geometry1: Geometry, geometry2: Geometry):
        self.geometry1 = geometry1
        self.geometry2 = geometry2

    def apply(self, sketch: adsk.fusion.Sketch):
        self.geometry1.draw(sketch)
        self.geometry2.draw(sketch)
        # Logic for intersection

    def calculate_area(self):
        # Logic to calculate intersected area
        pass
