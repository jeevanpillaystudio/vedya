import math
from .index import Transform
import adsk.core


class Scaling(Transform):
    def __init__(self, start_scale: float, end_scale: float):
        self.start_scale = start_scale
        self.end_scale = end_scale

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        scale_factor = self.start_scale + (self.end_scale - self.start_scale) * (
            index / (total - 1)
        )
        matrix = adsk.core.Matrix3D.create()
        matrix.setCell(0, 0, scale_factor)
        matrix.setCell(1, 1, scale_factor)
        return matrix
