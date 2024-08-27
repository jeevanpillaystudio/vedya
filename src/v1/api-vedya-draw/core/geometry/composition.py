from typing import List
# import adsk.fusion
# from .libs.component_utils import create_component
from .composition_geometry import CompositionGeometry

# only in xyPlane
class Composition:
    # top level only
    geometries: List[CompositionGeometry]
    base_plane_offset: float
    
    def __init__(self, plane_offset: float = 0.0):
        super().__init__()
        self.geometries: List[CompositionGeometry] = []
        self.base_plane_offset = plane_offset
        
    def add_geometry(self, geometry: CompositionGeometry, plane_offset: float = 0.0) -> None:
        geometry.plane_offset = self.base_plane_offset + plane_offset
        self.geometries.append(geometry)
        print(f"DEBUG: Added geometry {geometry} to composition")

    # def run(self, component: adsk.fusion.Component) -> None:
    #     for i, layer in enumerate(self.geometries):
    #         geometry_component = create_component(component, f"geometry-{i}")
    #         layer.run(geometry_component)

    def __str__(self):
        return f"Composition: {[str(geometry) for geometry in self.geometries]}"