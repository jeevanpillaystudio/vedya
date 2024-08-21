import adsk.core
from abc import ABC, abstractmethod


class Transform(ABC):
    @abstractmethod
    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        pass


class CompositeTransform(Transform):
    def __init__(self, *transforms: Transform):
        self.transforms = transforms

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        composite = adsk.core.Matrix3D.create()
        for transform in self.transforms:
            composite.transformBy(transform.get_matrix(index, total))
        return composite
