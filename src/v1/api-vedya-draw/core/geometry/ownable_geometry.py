from abc import abstractmethod
from typing import List
import uuid
from .geometry import Geometry
import adsk.fusion, adsk.core


class OwnableGeometry(Geometry):
    # header
    id: str

    # body
    parent: Geometry | None
    children: List[Geometry] = []
    center_x: float
    center_y: float

    def __init__(
        self,
        children: List[Geometry] = [],
        parent: Geometry | None = None,
        center_x: float = 0,
        center_y: float = 0,
    ):
        super().__init__()

        # id
        self.id = uuid.uuid4()

        # connect linked list
        self.children = children
        self.parent = parent
        self.center_x = center_x
        self.center_y = center_y
        self.plane_offset = 0

    @property
    def center_x(self):
        return self._center_x

    @center_x.setter
    def center_x(self, center_x: float):
        self._center_x = center_x

    @property
    def center_y(self):
        return self._center_y

    @center_y.setter
    def center_y(self, center_y: float):
        self._center_y = center_y

    @property
    def plane_offset(self):
        return self._plane_offset

    @plane_offset.setter
    def plane_offset(self, plane_offset: float):
        self._plane_offset = plane_offset

    @abstractmethod
    def run(self) -> adsk.fusion.BRepBodies:
        pass
