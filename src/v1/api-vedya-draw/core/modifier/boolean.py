import adsk.fusion

from ..geometry.index import ModifiableGeometry
from .index import Modifier


class Difference(Modifier):
    def __init__(self, subtracted_geometry: ModifiableGeometry):
        self.subtracted_geometry = subtracted_geometry

    def apply(self, sketch: adsk.fusion.Sketch, base_profile):
        # Draw the geometry to be subtracted
        subtracted_profile = self.subtracted_geometry.draw(sketch)

        # Apply any modifiers on the subtracted geometry
        subtracted_profile = self.subtracted_geometry.apply_modifiers(
            sketch, subtracted_profile
        )

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

    def calculate_area(self, base_area):
        # Note: This is a simplified calculation and may not be accurate for complex geometries
        subtracted_area = self.subtracted_geometry.calculate_area()
        return max(0, base_area - subtracted_area)

    def __str__(self):
        return f"Difference(subtracted_geometry={self.subtracted_geometry})"


class Intersect(Modifier):
    def __init__(self, intersecting_geometry: ModifiableGeometry):
        self.intersecting_geometry = intersecting_geometry
        self.intersected_profile = None

    def apply(self, sketch: adsk.fusion.Sketch, base_profile):
        # Draw the intersecting geometry
        intersecting_profile = self.intersecting_geometry.draw(sketch)

        # Apply any modifiers on the intersecting geometry
        intersecting_profile = self.intersecting_geometry.apply_modifiers(
            sketch, intersecting_profile
        )

        # Perform intersection
        if not base_profile or not intersecting_profile:
            raise ValueError("Invalid profiles for intersection")

        # Create a collection of profiles to intersect
        profile_collection = adsk.core.ObjectCollection.create()
        profile_collection.add(base_profile)
        profile_collection.add(intersecting_profile)

        # Perform the intersection
        intersected_profiles = sketch.profiles.intersect(profile_collection)

        if intersected_profiles.count != 1:
            raise ValueError("Unexpected number of profiles after intersection")

        self.intersected_profile = intersected_profiles.item(0)

        # Delete the original profiles
        base_profile.deleteMe()
        intersecting_profile.deleteMe()

        return self.intersected_profile

    def calculate_area(self):
        if not self.intersected_profile:
            raise ValueError("Intersection has not been applied yet")

        area_props = self.intersected_profile.areaProperties()
        return area_props.area

    def get_profile(self):
        return self.intersected_profile

    def __str__(self):
        return f"Intersection(intersecting_geometry={self.intersecting_geometry})"


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

    def calculate_area(self):
        # Note: This is still a simplified calculation and may not be accurate for overlapping geometries
        return sum(geometry.calculate_area() for geometry in self.geometries)

    def __str__(self):
        return f"Union({', '.join(str(g) for g in self.geometries)})"
