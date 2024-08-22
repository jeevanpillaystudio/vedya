import math
import adsk.core
import adsk.fusion

from .index import ModifiableGeometry


class Rectangle(ModifiableGeometry):
    def __init__(self, length: float, width: float, rotation: float = 0):
        super().__init__()
        self.length = length
        self.width = width
        self.rotation = rotation

    def draw(self, sketch: adsk.fusion.Sketch):
        if self.rotation == 0:
            profile = self._draw_rectangle(sketch, self.length, self.width)
        else:
            profile = self._draw_rotated_rectangle(
                sketch, self.length, self.width, self.rotation
            )

        # Apply modifiers
        # self.apply_modifiers(sketch)

        return profile

    def calculate_area(self):
        return self.length * self.width

    def _draw_rectangle(self, sketch: adsk.fusion.Sketch, length, width):
        return sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-length / 2, width / 2, 0),
            adsk.core.Point3D.create(length / 2, -width / 2, 0),
        )

    def _draw_rotated_rectangle(
        self, sketch: adsk.fusion.Sketch, length, width, rotation
    ):
        # Convert rotation to radians
        rotation_rad = math.radians(rotation)

        # Calculate rotated corner points
        half_length = length / 2
        half_width = width / 2
        corners = [
            (-half_length, half_width),
            (half_length, half_width),
            (half_length, -half_width),
            (-half_length, -half_width),
        ]

        rotated_corners = []
        for x, y in corners:
            rotated_x = x * math.cos(rotation_rad) - y * math.sin(rotation_rad)
            rotated_y = x * math.sin(rotation_rad) + y * math.cos(rotation_rad)
            rotated_corners.append(adsk.core.Point3D.create(rotated_x, rotated_y, 0))

        # Draw the rotated rectangle
        lines = sketch.sketchCurves.sketchLines
        for i in range(4):
            lines.addByTwoPoints(rotated_corners[i], rotated_corners[(i + 1) % 4])

        return sketch.profiles.item(sketch.profiles.count - 1)

    def __str__(self):
        return f"Rectangle(length={self.length}, width={self.width}, rotation={self.rotation})"


def calculate_rectangle_area(width, length):
    return width * length
