from typing import List
import adsk.fusion
from ...core.modifier.array import Array
from ...utils.lib import log
from ...core.geometry.index import Geometry, ModifiableGeometry
from ...core.component_utils import create_component


# @NOTE assuming all elements are on xYConstructionPlane
class CompositionGeometry(Geometry):
    def __init__(
        self,
        geometry: List[ModifiableGeometry],
        array_modifier: Array = None,
    ):
        self.geometries = geometry
        self.array_modifier = array_modifier or Array(1, 1)

    def draw(
        self,
        component: adsk.fusion.Component,
    ) -> None:
        for geometry in self.geometries:
            self.array_modifier.apply(geometry, component)

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.geometries])


class Composition:
    def __init__(self, layers: List[CompositionGeometry]):
        self.layers = layers

    def create(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.layers):
            geometry_component = create_component(component, f"geometry-{i}")
            layer.draw(geometry_component)
