from typing import List, Union as UnionType
import adsk.fusion, adsk.core
from ..component_utils import intersect_bodies
from ...utils.lib import log
from ..geometry_utils import create_sketch

from ..geometry.index import ModifiableGeometry
from .index import Modifier


class Boolean(Modifier):
    def __init__(
        self, geometries: UnionType[ModifiableGeometry, List[ModifiableGeometry]]
    ):
        self.geometries = (
            [geometries] if isinstance(geometries, ModifiableGeometry) else geometries
        )
        self.operation_type = None  # To be set by subclasses

    def apply(
        self,
        component: adsk.fusion.Component,
        base_body: adsk.fusion.BRepBody,
        extra_plane_offset: float = 0,
    ) -> adsk.fusion.BRepBody:
        tool_bodies = adsk.core.ObjectCollection.create()

        for geometry in self.geometries:
            geometry.pre_draw(component, extra_plane_offset=extra_plane_offset)
            geometry.draw()
            tool_body = geometry.post_draw(component=component)
            tool_bodies.add(tool_body)

        if not base_body or tool_bodies.count == 0:
            raise ValueError(
                f"Invalid bodies for {self.__class__.__name__.lower()} operation"
            )

        result_body = intersect_bodies(
            root_component=component,
            target_body=base_body,
            tool_bodies=tool_bodies,
            operation=self.operation_type,
        )

        # Clean up the temporary tool bodies
        # for i in range(tool_bodies.count):
        #     tool_bodies.item(i).deleteMe()

        return result_body

    def __str__(self):
        return (
            f"{self.__class__.__name__}({', '.join(str(g) for g in self.geometries)})"
        )


class Intersect(Boolean):
    def __init__(self, geometry: ModifiableGeometry):
        super().__init__(geometry)
        self.operation_type = adsk.fusion.FeatureOperations.IntersectFeatureOperation


class Difference(Boolean):
    def __init__(self, geometry: ModifiableGeometry):
        super().__init__(geometry)
        self.operation_type = adsk.fusion.FeatureOperations.CutFeatureOperation


class Union(Boolean):
    def __init__(self, *geometries: ModifiableGeometry):
        super().__init__(geometries)
        self.operation_type = adsk.fusion.FeatureOperations.JoinFeatureOperation
