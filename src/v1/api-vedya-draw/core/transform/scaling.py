import math
from .index import Transform
import adsk.core


class Scaling(Transform):
    def __init__(self, scale_factor: float):
        self.scale_factor = scale_factor

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        scale = self.scale_factor**index
        matrix = adsk.core.Matrix3D.create()
        matrix.setCell(0, 0, scale)
        matrix.setCell(1, 1, scale)
        return matrix
