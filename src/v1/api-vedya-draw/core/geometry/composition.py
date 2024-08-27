from typing import List
# import adsk.fusion
# from .libs.component_utils import create_component
from .composition_geometry import CompositionGeometry


class Composition:
    extrude: bool

    def __init__(self, geometries: List[CompositionGeometry]):
        super().__init__()
        self.geometries = geometries

    # def run(self, component: adsk.fusion.Component) -> None:
    #     for i, layer in enumerate(self.geometries):
    #         geometry_component = create_component(component, f"geometry-{i}")
    #         layer.run(geometry_component)

    def __str__(self):
        return f"Composition: {[str(geometry) for geometry in self.geometries]}"