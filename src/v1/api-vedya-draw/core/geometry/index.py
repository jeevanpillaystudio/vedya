# Base Layer: Geometry
from typing import List
import adsk.fusion
from abc import ABC, abstractmethod

from ...utils.lib import log

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
    ) -> adsk.fusion.BRepBody:
        body = None

        # Extr
        if self.extrude_height > 0:
            body = extrude_profile_by_area(
                component=component,
                profiles=profiles,
                area=self.calculate_area(),
                extrude_height=self.extrude_height,
                name="draw-extrude",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            ).item(0)

        # Apply modifiers
        for modifier in self.modifier_stack:
            log(f"Applying modifier: {modifier}")
            modifier.apply(component, body)

        return body

    def add_modifier(self, modifier):
        self.modifier_stack.append(modifier)
        return self
