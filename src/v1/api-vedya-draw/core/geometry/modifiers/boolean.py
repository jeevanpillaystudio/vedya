from typing import List, Union as UnionType
import adsk.fusion, adsk.core
from ..libs.component_utils import intersect_bodies

# from core.geometry.libs.component_utils import intersect_bodies
from ...utils import log

# from core.geometry.composition_geometry import CompositionGeometry

# from ..libs.component_utils import intersect_bodies
from ..ownable_geometry import OwnableGeometry


class Boolean:
    def __init__(self, geometries: UnionType[OwnableGeometry, List[OwnableGeometry]]):
        self.geometries = (
            [geometries] if isinstance(geometries, OwnableGeometry) else geometries
        )
        self.operation_type = None  # To be set by subclasses

    def run(
        self,
        component: adsk.fusion.Component,
        body: adsk.fusion.BRepBody,
        tool_bodies: adsk.fusion.BRepBodies,
    ):
        intersect_bodies(
            root_component=component,
            target_body=body,
            tool_bodies=tool_bodies,
            operation=self.operation_type,
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}({', '.join(str(g) for g in self.geometries)})"
        )


class Intersect(Boolean):
    def __init__(self, geometry: OwnableGeometry):
        super().__init__(geometry)
        self.operation_type = adsk.fusion.FeatureOperations.IntersectFeatureOperation


class Difference(Boolean):
    def __init__(self, geometry: OwnableGeometry):
        super().__init__(geometry)
        self.operation_type = adsk.fusion.FeatureOperations.CutFeatureOperation


class Union(Boolean):
    def __init__(self, *geometries: OwnableGeometry):
        super().__init__(geometries)
        self.operation_type = adsk.fusion.FeatureOperations.JoinFeatureOperation
