import adsk.core
from abc import ABC, abstractmethod


class Transform(ABC):
    @abstractmethod
    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        pass
