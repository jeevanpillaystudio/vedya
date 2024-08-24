# Base Layer: Geometry
from typing import List
import adsk.fusion
from abc import ABC, abstractmethod

from ...utils.lib import log

from ...core.modifier.index import Modifier
from ..geometry_utils import create_offset_plane, create_sketch, extrude_profile_by_area
import adsk.fusion


class Geometry(ABC):
    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self) -> float:
        pass


class ModifiableGeometry(Geometry):
    def __init__(
        self, thickness: float, plane_offset: float = 0, modifier: Modifier = None
    ):
        self.modifer = modifier
        self.extrude_height = thickness
        self.sketch = None
        self.plane_offset = plane_offset

    @abstractmethod
    def calculate_area(self) -> float:
        pass

    def pre_draw(self, component: adsk.fusion.Component, extra_plane_offset: float = 0):
        self.sketch = create_sketch(component=component, offset=self.plane_offset + extra_plane_offset, name="layer-sketch")

    @abstractmethod
    def draw(self):
        pass

    def post_draw(self, component: adsk.fusion.Component) -> adsk.fusion.BRepBody:
        body = None

        # Extr
        if self.extrude_height > 0:
            body = extrude_profile_by_area(
                component=component,
                profiles=self.sketch.profiles,
                area=self.calculate_area(),
                extrude_height=self.extrude_height,
                name="draw-extrude",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            ).item(0)

        # Apply modifiers
        if self.modifer:
            body = self.modifer.apply(component, body)

        return body
