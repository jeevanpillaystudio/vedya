import math
from .index import Transform
import adsk.core


class Rotation(Transform):
    def __init__(self, x: float, y: float, z: float):
        self.x = math.radians(x)
        self.y = math.radians(y)
        self.z = math.radians(z)

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        # Calculate the fraction of rotation to apply
        fraction = index / (total - 1) if total > 1 else 1

        # Create rotation matrices for each axis
        rx = adsk.core.Matrix3D.create()
        ry = adsk.core.Matrix3D.create()
        rz = adsk.core.Matrix3D.create()

        # Set up X rotation
        cx = math.cos(self.x * fraction)
        sx = math.sin(self.x * fraction)
        rx.setCell(1, 1, cx)
        rx.setCell(1, 2, -sx)
        rx.setCell(2, 1, sx)
        rx.setCell(2, 2, cx)

        # Set up Y rotation
        cy = math.cos(self.y * fraction)
        sy = math.sin(self.y * fraction)
        ry.setCell(0, 0, cy)
        ry.setCell(0, 2, sy)
        ry.setCell(2, 0, -sy)
        ry.setCell(2, 2, cy)

        # Set up Z rotation
        cz = math.cos(self.z * fraction)
        sz = math.sin(self.z * fraction)
        rz.setCell(0, 0, cz)
        rz.setCell(0, 1, -sz)
        rz.setCell(1, 0, sz)
        rz.setCell(1, 1, cz)

        # Combine rotations (order: Z * Y * X)
        result = adsk.core.Matrix3D.create()
        result.transformBy(rx)
        result.transformBy(ry)
        result.transformBy(rz)

        return result
