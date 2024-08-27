from typing import List
import adsk.fusion, adsk.core
from .composition_geometry import CompositionGeometry


# only in xyPlane
class Composition:
    # top level only
    root_comp: adsk.fusion.Component
    geometries: List[CompositionGeometry]
    base_plane_offset: float

    def __init__(
        self,
        root_comp: adsk.fusion.Component,
        plane_offset: float = 0.0,
    ):
        super().__init__()
        self.root_comp = root_comp
        self.geometries: List[CompositionGeometry] = []
        self.base_plane_offset = plane_offset

    def add_geometry(
        self, geometry: CompositionGeometry, plane_offset: float = 0.0
    ) -> None:
        self.geometries.append(geometry)
        print(f"DEBUG: Added geometry {geometry} to composition")

    def create(self) -> None:
        for i, geometry in enumerate(self.geometries):
            geometry.setup(self.root_comp)
            geometry.run()

    def __str__(self):
        return f"Composition: {[str(geometry) for geometry in self.geometries]}"
