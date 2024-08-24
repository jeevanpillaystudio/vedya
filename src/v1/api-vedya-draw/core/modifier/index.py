# Middle Layer: Design Patterns
import adsk.fusion
from abc import ABC, abstractmethod


class Modifier(ABC):
    @abstractmethod
    def apply(self, sketch: adsk.fusion.Sketch):
        pass
