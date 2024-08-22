from typing import Generic, TypeVar, List
import adsk.fusion

from ...core.geometry.index import Geometry
from ...core.transform.index import Transform, CompositeTransform
from ...core.transform.translation import Translation
from ...core.transform.rotation import Rotation
from ...core.transform.scaling import Scaling


T = TypeVar("T", bound=Geometry)


class Array(Generic[T]):
    def __init__(self, base_geometry: T, count: int):
        self.base_geometry = base_geometry
        self.count = count
        self.offset = Translation(0, 0, 0)
        self.rotation = Rotation(0, 0, 0)
        self.scale = Scaling(1, 1)
        self.elements: List[T] = []

    def set_offset(self, x: float, y: float, z: float):
        self.offset = Translation(x, y, z)

    def set_rotation(self, x: float, y: float, z: float):
        self.rotation = Rotation(x, y, z)

    def set_scale(self, start: float, end: float):
        self.scale = Scaling(start, end)

    def preview(self, sketch: adsk.fusion.Sketch):
        transform = CompositeTransform(self.offset, self.rotation, self.scale)
        for i in range(self.count):
            matrix = transform.get_matrix(i, self.count)
            transformed_geometry = self.base_geometry.transform(matrix)
            transformed_geometry.draw(sketch)

    def apply(self, sketch: adsk.fusion.Sketch):
        self.elements = []
        transform = CompositeTransform(self.offset, self.rotation, self.scale)
        for i in range(self.count):
            matrix = transform.get_matrix(i, self.count)
            transformed_geometry = self.base_geometry.transform(matrix)
            self.elements.append(transformed_geometry)
            transformed_geometry.draw(sketch)

    def calculate_area(self) -> float:
        return sum(element.calculate_area() for element in self.elements)
