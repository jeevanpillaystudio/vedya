import adsk.core
from .index import Geometry


class Tessellate(Geometry):
    def __init__(
        self, base_geometry: Geometry, rows: int, columns: int, spacing: float
    ):
        self.base_geometry = base_geometry
        self.rows = rows
        self.columns = columns
        self.spacing = spacing

    def draw(self, sketch: adsk.fusion.Sketch):
        # Implementation for tessellating the base geometry
        pass

    def calculate_area(self):
        return self.base_geometry.calculate_area() * self.rows * self.columns


def draw_tesseract_projection(sketch, center_x, center_y, size):
    outer_cube_points = []
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            for dz in [-1, 1]:
                x = center_x + size * dx / 2
                y = center_y + size * dy / 2
                z = size * dz / 2
                outer_cube_points.append([x, y, z])

    inner_cube_points = []
    scale_factor = 0.5
    for point in outer_cube_points:
        x, y, z = point
        x = center_x + (x - center_x) * scale_factor
        y = center_y + (y - center_y) * scale_factor
        z = z * scale_factor
        inner_cube_points.append([x, y, z])

    for i in range(8):
        start_point = outer_cube_points[i]
        for j in range(i + 1, 8):
            end_point = outer_cube_points[j]
            if (
                sum(1 for start, end in zip(start_point, end_point) if start == end)
                == 2
            ):
                sketch.sketchCurves.sketchLines.addByTwoPoints(
                    adsk.core.Point3D.create(*start_point[:-1]),
                    adsk.core.Point3D.create(*end_point[:-1]),
                )

    for i in range(8):
        start_point_outer = outer_cube_points[i]
        start_point_inner = inner_cube_points[i]
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(*start_point_outer[:-1]),
            adsk.core.Point3D.create(*start_point_inner[:-1]),
        )
        for j in range(i + 1, 8):
            end_point_inner = inner_cube_points[j]
            if (
                sum(
                    1
                    for start, end in zip(start_point_inner, end_point_inner)
                    if start == end
                )
                == 2
            ):
                sketch.sketchCurves.sketchLines.addByTwoPoints(
                    adsk.core.Point3D.create(*start_point_inner[:-1]),
                    adsk.core.Point3D.create(*end_point_inner[:-1]),
                )
