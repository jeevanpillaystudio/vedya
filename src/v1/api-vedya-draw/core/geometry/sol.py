import adsk.fusion

from .circle import Circle
from .index import Geometry
from ..transform.radial import Radial
from ..modifier.array import Array


class SeedOfLife(Geometry):
    def __init__(self, radius: float, num_circles: int = 6):
        self.radius = radius
        self.num_circles = num_circles
        self.center_circle = Circle(radius)
        self.outer_circles = Array(Circle(radius), num_circles, Radial(radius))

    def draw(self, sketch: adsk.fusion.Sketch):
        self.center_circle.draw(sketch)
        self.outer_circles.apply(sketch)

    def calculate_area(self):
        return self.center_circle.calculate_area() + self.outer_circles.calculate_area()
