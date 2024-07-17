from solid2 import *
import numpy as np
from . import *

def create_cylinder_with_filled_circle(L, H, R, resolution):
    """Creates a 3D model of a cylinder with a filled circle on the surface."""
    points = transform_rectangle_to_cylinder(L, H, R, resolution)
    
    # Create cylinder
    cylinder_shell = cylinder(r=R, h=H)

    # Add points as small spheres to represent the filled circle
    # spheres = [translate([x, y, z])(sphere(r=resolution/2)) for x, y, z in points]
    # return union()(cylinder_shell, *spheres)

    return cylinder_shell

def create_cylinder_scad_model(L, H, R, resolution):
    # Create the 3D model
    cylinder_model = create_cylinder_with_filled_circle(L, H, R, resolution)

    # Render to an OpenSCAD file
    scad_render_to_file(cylinder_model, 'cylindrical_model.scad')

__all__ = ["create_cylinder_scad_model"]