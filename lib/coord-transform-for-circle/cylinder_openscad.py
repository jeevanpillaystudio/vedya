from solid2 import *
import numpy as np

def transform_to_cylinder(x, y, L, R):
    """Transforms a single point (x, y) on the rectangle into cylindrical coordinates."""
    theta = 2 * np.pi * x / L
    x_prime = R * np.cos(theta)
    y_prime = R * np.sin(theta)
    z_prime = y
    return x_prime, y_prime, z_prime

def transform_rectangle_to_cylinder(L, H, R, resolution):
    """Transforms points of a pixelated rectangle into cylindrical coordinates."""
    x_steps = int(L / resolution)
    y_steps = int(H / resolution)

    points = []
    for i in range(x_steps):
        for j in range(y_steps):
            x = i * resolution + resolution / 2
            y = j * resolution + resolution / 2
            x_prime, y_prime, z_prime = transform_to_cylinder(x, y, L, R)
            points.append((x_prime, y_prime, z_prime))
    
    return points

def create_cylinder_with_filled_circle(L, H, R, resolution):
    """Creates a 3D model of a cylinder with a filled circle on the surface."""
    points = transform_rectangle_to_cylinder(L, H, R, resolution)
    
    # Create cylinder
    cylinder_shell = cylinder(r=R, h=H)

    # Add points as small spheres to represent the filled circle
    spheres = [translate([x, y, z])(sphere(r=resolution/2)) for x, y, z in points]

    return union()(cylinder_shell, *spheres)

def create_cylinder_scad_model(L, H, R, resolution):
    # Create the 3D model
    cylinder_model = create_cylinder_with_filled_circle(L, H, R, resolution)

    # Render to an OpenSCAD file
    scad_render_to_file(cylinder_model, 'cylindrical_model.scad')

__all__ = ["create_cylinder_scad_model"]
    
