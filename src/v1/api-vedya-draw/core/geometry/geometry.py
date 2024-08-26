# Base Layer: Geometry
from typing import List
import uuid
import adsk.fusion, adsk.core
from abc import ABC, abstractmethod


class Geometry(ABC):
    def __init__(self, center_x: float = 0, center_y: float = 0, thickness: float = 0):
        self.center_x = center_x
        self.center_y = center_y
        self.thickness = thickness

    @abstractmethod
    def calculate_area(self) -> float:
        pass

    @abstractmethod
    def run(self):
        pass

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
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float):
        self._thickness = thickness


class OwnableGeometry(Geometry):
    # header
    id: str

    # body
    parent: Geometry | None
    children: List[Geometry] = []

    def __init__(
        self,
        children: List[Geometry] = [],
        parent: Geometry | None = None,
        thickness: float = 0,
        center_x: float = 0,
        center_y: float = 0,
    ):
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            thickness=thickness,
        )

        # id
        self.id = uuid.uuid4()

        # connect linked list
        self.children = children
        self.parent = parent

    @property
    def center_x(self):
        return super().center_x + self.parent.center_x if self.parent else 0

    @property
    def center_y(self):
        return super().center_y + self.parent.center_y if self.parent else 0
