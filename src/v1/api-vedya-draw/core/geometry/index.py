# Base Layer: Geometry
from typing import List
import adsk.fusion
from abc import ABC, abstractmethod

from ...core.modifier.index import Modifier
from ..geometry_utils import extrude_profile_by_area
import adsk.fusion


class Geometry(ABC):
    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self) -> float:
        pass


class ModifiableGeometry(Geometry):
    def __init__(self, extrude_height: float):
        self.modifier_stack: List[Modifier] = []
        self.extrude_height = extrude_height

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self) -> float:
        pass

    def post_draw(
        self, component: adsk.fusion.Component, profiles: List[adsk.fusion.Profile]
    ):
        if self.extrude_height > 0:
            extrude_profile_by_area(
                component=component,
                profiles=profiles,
                area=self.calculate_area(),
                extrude_height=self.extrude_height,
                name="draw-extrude",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            )

    def add_modifier(self, modifier):
        self.modifier_stack.append(modifier)
        return self

    # # @TODO fix this? not sure
    def apply_modifiers(self, sketch: adsk.fusion.Sketch):
        for modifier in self.modifier_stack:
            modifier.apply(sketch)
