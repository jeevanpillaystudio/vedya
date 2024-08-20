import adsk.core
import math


def create_astroid_points(n, numPoints, scaleX, scaleY):
    points = adsk.core.ObjectCollection.create()
    for i in range(numPoints + 1):
        angle = i * 2 * math.pi / numPoints
        x = (
            pow(abs(math.cos(angle)), 2 / n)
            * math.copysign(1, math.cos(angle))
            * scaleX
        )
        y = (
            pow(abs(math.sin(angle)), 2 / n)
            * math.copysign(1, math.sin(angle))
            * scaleY
        )
        points.add(adsk.core.Point3D.create(x, y, 0))
    return points


def draw_astroid(sketch, n, numPoints, scaleX, scaleY):
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(n, numPoints, scaleX, scaleY)
    )


def draw_astroid_stroke(sketch, n, numPoints, scaleX, scaleY, strokeWeight):
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(n, numPoints, scaleX, scaleY)
    )
    sketch.sketchCurves.sketchFittedSplines.add(
        create_astroid_points(
            n, numPoints, scaleX - strokeWeight, scaleY - strokeWeight
        )
    )


def calculate_astroid_area(scaleX):
    return (3 / 8) * math.pi * scaleX**2
