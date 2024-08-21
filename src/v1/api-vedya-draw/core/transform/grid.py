import math
from .index import Transform
import adsk.core


class Grid(Transform):
    def __init__(self, rows: int, columns: int, spacing: float):
        self.rows = rows
        self.columns = columns
        self.spacing = spacing

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        row = index // self.columns
        col = index % self.columns
        x = (col - (self.columns - 1) / 2) * self.spacing
        y = (row - (self.rows - 1) / 2) * self.spacing
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(x, y, 0)
        return matrix
