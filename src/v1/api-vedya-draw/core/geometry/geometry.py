# Base Layer: Geometry
from typing import List
from abc import ABC, abstractmethod
import adsk.fusion, adsk.core


class Geometry(ABC):
    def __init__(self, center_x: float = 0, center_y: float = 0):
        self.center_x = center_x
        self.center_y = center_y

    @abstractmethod
    def calculate_area(self) -> float:
        pass

    @abstractmethod
    def run(self) -> adsk.fusion.BRepBodies:
        pass
