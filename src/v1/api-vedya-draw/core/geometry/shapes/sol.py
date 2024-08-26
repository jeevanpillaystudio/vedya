import adsk.fusion

from typing import List
from .circle import Circle
from .core.geometry import Geometry
from ..transform.radial import Radial
from ..modifier.array import Array


class SeedOfLife(Geometry):
    def __init__(self, radius: float, num_circles: int = 6):
        self.radius = radius
        self.num_circles = num_circles
        self.center_circle: Geometry = Circle(radius)
        self.outer_circles: Array[Geometry] = Array(
            Circle(radius), num_circles, Radial(radius)
        )

    def run(self, sketch: adsk.fusion.Sketch):
        # Create a collection to store all circles
        all_circles: List[Geometry] = [self.center_circle] + self.outer_circles.elements

        # Draw all circles in a single loop
        for circle in all_circles:
            circle.run(sketch)

    def calculate_area(self):
        return self.center_circle.calculate_area() + self.outer_circles.calculate_area()
