from .index import Transform
import adsk.core


class Translation(Transform):
    def __init__(self, x: float, y: float, z: float):
        """
        Initialize a Translation transform.

        :param x: Translation along X-axis
        :param y: Translation along Y-axis
        :param z: Translation along Z-axis
        """
        self.x = x
        self.y = y
        self.z = z

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        """
        Get the translation matrix for the given index in the array.

        :param index: Current index in the array
        :param total: Total number of elements in the array
        :return: 3D translation matrix
        """
        # Calculate the translation to apply
        tx = self.x * index
        ty = self.y * index
        tz = self.z * index

        # Create and set up the translation matrix
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(tx, ty, tz)

        return matrix

    def set_offset(self, x: float, y: float, z: float):
        """
        Set a new offset for the translation.

        :param x: New X offset
        :param y: New Y offset
        :param z: New Z offset
        """
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Translation(x={self.x}, y={self.y}, z={self.z})"
