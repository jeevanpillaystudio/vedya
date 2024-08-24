# Base Layer: Geometry
from typing import List
import adsk.fusion, adsk.core
from abc import ABC, abstractmethod

from ...core.modifier.index import Modifier
from ..geometry_utils import create_sketch, extrude_profile_by_area


class Geometry(ABC):
    def __init__(self, center_x: float = 0, center_y: float = 0, thickness: float = 0):
        self.center_x = center_x
        self.center_y = center_y
        self.thickness = thickness

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    @abstractmethod
    def calculate_area(self) -> float:
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


class ModifiableGeometry(Geometry):
    def __init__(
        self,
        thickness: float,
        plane_offset: float = 0,
        modifier: Modifier = None,
        center_x: float = 0,
        center_y: float = 0,
    ):
        super().__init__(center_x, center_y, thickness)
        self.modifer = modifier

        # @TODO: remove; where to put...
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
        if not self.thickness > 0:
            raise NotImplementedError("Extrusion not implemented")

        # extrude
        body = extrude_profile_by_area(
            component=component,
            profiles=self.sketch.profiles,
            area=self.calculate_area(),
            extrude_height=self.thickness,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        ).item(0)

        # modifier checker
        if self.modifer:
            # modify: re. only apply modifier after drawn
            body = self.modifer.apply(
                component,
                body,
                parent_center_x=self.center_x,
                parent_center_y=self.center_y,
            )

        # return
        return body

    def set_plane_offset(self, offset: float):
        self.plane_offset = offset

    @abstractmethod
    def xyBound(self) -> adsk.core.Point3D:
        pass
