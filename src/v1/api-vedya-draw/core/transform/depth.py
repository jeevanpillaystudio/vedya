import adsk.core
from .index import Transform


class DepthRepeat:
    Increment = 0
    Decrement = 1


class Depth(Transform):
    def __init__(self, total_depth: float, direction: int):
        self.total_depth = total_depth
        self.direction = direction

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        if self.direction == DepthRepeat.Decrement:
            depth_factor = (total - index) / total
        else:
            depth_factor = index / total

        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(
            0, 0, self.total_depth * depth_factor
        )
        return matrix
