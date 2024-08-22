# Base Layer: Geometry
from ..modifier.stack import ModifierStack
import adsk.fusion
from abc import ABC, abstractmethod


class Geometry(ABC):
    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self):
        pass


class ModifiableGeometry(Geometry):
    def __init__(self):
        self.modifier_stack = ModifierStack()

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self):
        pass

    def add_modifier(self, modifier):
        self.modifier_stack.add_modifier(modifier)

    def apply_modifiers(
        self, sketch: adsk.fusion.Sketch, profile: adsk.fusion.Profile
    ) -> adsk.fusion.Profile:
        return self.modifier_stack.apply(sketch, profile)
