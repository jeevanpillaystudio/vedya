# Base Layer: Geometry
from typing import List
import adsk.fusion, adsk.core
from abc import ABC, abstractmethod

from ...core.modifier.index import Modifier
from ..geometry_utils import create_sketch, extrude_profile_by_area


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

    def pre_draw(self, component: adsk.fusion.Component = None):
        self.sketch = create_sketch(
            component=component,
            offset=self.plane_offset,
            name="layer-sketch",
        )

    @abstractmethod
    def draw(self):
        pass

    def post_draw(self, component: adsk.fusion.Component) -> adsk.fusion.BRepBody:
        # extrude checker
        if not self.extrude_height > 0:
            raise NotImplementedError("Extrusion not implemented")

        # extrude
        body = extrude_profile_by_area(
            component=component,
            profiles=self.sketch.profiles,
            area=self.calculate_area(),
            extrude_height=self.extrude_height,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        ).item(0)

        # modifier checker
        if self.modifer:
            # modify: re. only apply modifier after drawn
            body = self.modifer.apply(component, body, plane_offset=self.plane_offset)

        # return
        return body

    def set_plane_offset(self, offset: float):
        self.plane_offset = offset

    @abstractmethod
    def xyBound(self) -> adsk.core.Point3D:
        pass
