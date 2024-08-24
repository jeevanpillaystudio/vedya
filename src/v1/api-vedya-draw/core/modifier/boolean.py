from typing import List
import adsk.fusion, adsk.core
from ..component_utils import intersect_bodies
from ...utils.lib import log
from ..geometry_utils import create_sketch

from ..geometry.index import ModifiableGeometry
from .index import Modifier


class Intersect(Modifier):
    def __init__(self, subtracted_geometry: ModifiableGeometry):
        self.subtracted_geometry = subtracted_geometry

    def apply(self, sketch: adsk.fusion.Sketch, base_profile):
        # Draw the geometry to be subtracted
        subtracted_profile = self.subtracted_geometry.draw(sketch)

        # Apply any modifiers on the subtracted geometry
        # subtracted_profile = self.subtracted_geometry.apply_modifiers(
        #     sketch, subtracted_profile
        # )

        # Perform the subtraction operation
        if not base_profile or not subtracted_profile:
            raise ValueError("Invalid profiles for difference operation")

        # Create a collection of profiles to subtract
        profile_collection = adsk.core.ObjectCollection.create()
        profile_collection.add(base_profile)
        profile_collection.add(subtracted_profile)

        # Perform the subtraction
        result = sketch.profiles.add(
            profile_collection, False
        )  # False for subtraction operation

        # Delete the original profiles
        base_profile.deleteMe()
        subtracted_profile.deleteMe()

        return result

    def __str__(self):
        return f"Difference(subtracted_geometry={self.subtracted_geometry})"


class Difference(Modifier):
    def __init__(self, subtracted_geometry: ModifiableGeometry):
        self.subtracted_geometry = subtracted_geometry

    def apply(
        self,
        component: adsk.fusion.Component,
        base_body: adsk.fusion.BRepBody,
    ) -> adsk.fusion.Profile:
        # Create a sketch for the subtracted geometry
        sketch = create_sketch(component, "subtraction_sketch")
        self.subtracted_geometry.draw(sketch)
        tool_body = self.subtracted_geometry.post_draw(
            component=component, profiles=sketch.profiles
        )

        if not base_body or not tool_body:
            raise ValueError("Invalid profiles for difference operation")

        # Perform subtraction
        tool_bodies = adsk.core.ObjectCollection.create()
        tool_bodies.add(tool_body)
        intersect_bodies(
            root_component=component,
            target_body=base_body,
            tool_bodies=tool_bodies,
            operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
        )

        # Clean up the temporary tool body
        # @TODO wtf is this?
        # tool_body.deleteMe()

    def __str__(self):
        return f"Difference(subtracted_geometry={self.subtracted_geometry})"


class Union(Modifier):
    def __init__(self, *geometries: ModifiableGeometry):
        self.geometries = geometries

    def apply(self, sketch: adsk.fusion.Sketch, base_profile):
        # Create a collection to store all profiles
        profile_collection = adsk.core.ObjectCollection.create()
        profile_collection.add(base_profile)

        # Draw all additional geometries and add their profiles to the collection
        for geometry in self.geometries:
            profile = geometry.draw(sketch)
            profile = geometry.apply_modifiers(sketch, profile)
            profile_collection.add(profile)

        # Perform the union operation
        result = sketch.profiles.add(
            profile_collection, True
        )  # True for union operation

        # Delete the original profiles
        for i in range(sketch.profiles.count - 1, -1, -1):
            if sketch.profiles.item(i) != result:
                sketch.profiles.item(i).deleteMe()

        return result


def __str__(self):
    return f"Union({', '.join(str(g) for g in self.geometries)})"
