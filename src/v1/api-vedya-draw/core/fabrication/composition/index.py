from typing import List
import adsk.fusion
from ...geometry.action.action import Action
from .composition_geometry import CompositionGeometry
from ...component_utils import create_component


class Composition(Action):
    extrude: bool

    def __init__(self, geometries: List[CompositionGeometry], extrude: bool = False):
        super().__init__()
        self.geometries = geometries
        self.extrude = extrude

    def run(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.geometries):
            geometry_component = create_component(component, f"geometry-{i}")
            layer.run(geometry_component)
