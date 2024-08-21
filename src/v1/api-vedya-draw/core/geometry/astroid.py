import adsk.core
import math

from .index import Geometry


class Astroid(Geometry):
    def __init__(self, n, num_points, scale_x, scale_y):
        self.n = n
        self.num_points = num_points
        self.scale_x = scale_x
        self.scale_y = scale_y

    def draw(self, sketch):
        sketch.sketchCurves.sketchFittedSplines.add(
            create_astroid_points(self.n, self.num_points, self.scale_x, self.scale_y)
        )


def create_astroid_points(n, num_points, scale_x, scale_y):
    points = adsk.core.ObjectCollection.create()
    for i in range(num_points + 1):
        angle = i * 2 * math.pi / num_points
        x = (
            pow(abs(math.cos(angle)), 2 / n)
            * math.copysign(1, math.cos(angle))
            * scale_x
        )
        y = (
            pow(abs(math.sin(angle)), 2 / n)
            * math.copysign(1, math.sin(angle))
            * scale_y
        )
        points.add(adsk.core.Point3D.create(x, y, 0))
    return points


def draw_astroid(sketch, n, num_points, scale_x, scale_y):
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(n, num_points, scale_x, scale_y)
    )


def draw_astroid_stroke(sketch, n, num_points, scale_x, scale_y, thickness):
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(n, num_points, scale_x, scale_y)
    )
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(n, num_points, scale_x - thickness, scale_y - thickness)
    )


def calculate_astroid_area(scale_x):
    return (3 / 8) * math.pi * scale_x**2
