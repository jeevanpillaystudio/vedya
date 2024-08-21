import math
from .index import Transform
import adsk.core


class Radial(Transform):
    def __init__(self, radius: float):
        self.radius = radius

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        angle = (2 * math.pi * index) / total
        x = self.radius * math.cos(angle)
        y = self.radius * math.sin(angle)
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(x, y, 0)
        return matrix
