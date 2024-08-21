# Middle Layer: Design Patterns
import adsk.fusion
from abc import abstractmethod
import abc


class Modifier(abc):
    @abstractmethod
    def apply(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self):
        pass
