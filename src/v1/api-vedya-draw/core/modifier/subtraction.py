import adsk.fusion

from ..geometry.index import Geometry
from .index import Modifier


class Subtraction(Modifier):
    def __init__(self, base_geometry: Geometry, subtracted_geometry: Geometry):
        self.base_geometry = base_geometry
        self.subtracted_geometry = subtracted_geometry

    def apply(self, sketch: adsk.fusion.Sketch):
        self.base_geometry.draw(sketch)
        self.subtracted_geometry.draw(sketch)
        # Logic for subtraction

    def calculate_area(self):
        # Logic to calculate area after subtraction
        pass
