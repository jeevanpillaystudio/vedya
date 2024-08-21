# Base Layer: Geometry
import adsk.fusion
from abc import ABC, abstractmethod


class Geometry(ABC):
    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self):
        pass
