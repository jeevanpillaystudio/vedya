import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# References:
# 1. Cylindrical Coordinates: https://mathinsight.org/cylindrical_coordinates
# 2. Transformations between coordinate systems: https://en.wikipedia.org/wiki/Coordinate_system#Transformations_between_coordinate_systems
# 3. Plotting with Matplotlib: https://matplotlib.org/stable/gallery/mplot3d/index.html

def transform_to_cylinder(x, y, L, R):
    """Transforms a single point (x, y) on the rectangle into cylindrical coordinates.

    Args:
        x (float): The x-coordinate on the rectangle.
        y (float): The y-coordinate on the rectangle.
        L (float): The length of the rectangle.
        R (float): The radius of the cylinder.

    Returns:
        tuple: The transformed coordinates (x', y', z') in cylindrical space.

    Reference:
    This transformation maps a rectangular coordinate (x, y) to cylindrical coordinates (x', y', z').
    For more details, see: https://mathinsight.org/cylindrical_coordinates
    """
    theta = 2 * np.pi * x / L
    x_prime = R * np.cos(theta)
    y_prime = R * np.sin(theta)
    z_prime = y
    return x_prime, y_prime, z_prime

def transform_circle_to_cylinder(L, R, circle_radius, circle_height, resolution):
    """Transforms points of a filled circle into cylindrical coordinates.

    Args:
        L (float): The length of the rectangle.
        R (float): The radius of the cylinder.
        circle_radius (float): The radius of the circle.
        circle_height (float): The height position of the circle on the cylinder.
        resolution (float): The resolution of the circle filling.

    Returns:
        list: List of transformed points (x', y', z') in cylindrical coordinates.

    Reference:
    This function fills a circle on a cylindrical surface by iterating over the radius and angle.
    For more details on cylindrical coordinates and their applications, see: https://en.wikipedia.org/wiki/Coordinate_system#Transformations_between_coordinate_systems
    """
    num_r_steps = int(2 * circle_radius / resolution)
    num_theta_steps = int(2 * np.pi * circle_radius / resolution)

    points = []
    for j in range(num_r_steps):
        for k in range(num_theta_steps):
            r = circle_radius * (j * resolution / (2 * circle_radius))
            theta = 2 * np.pi * k / num_theta_steps
            x = r * np.cos(theta)
            y = circle_height + r * np.sin(theta)
            z = circle_height + r * np.cos(theta)
            x_prime, y_prime, z_prime = transform_to_cylinder(x, y, L, R)
            points.append((x_prime, y_prime, z_prime))

    return points

def transform_rectangle_to_cylinder(L, H, R, resolution):
    """Transforms points of a pixelated rectangle into cylindrical coordinates.

    Args:
        L (float): The length of the rectangle.
        H (float): The height of the rectangle.
        R (float): The radius of the cylinder.
        resolution (float): The resolution of the pixelation.

    Returns:
        list: List of transformed points (x', y', z') in cylindrical coordinates.

    Reference:
    This function uses a pixelated approach to plot points on a cylindrical surface.
    For more details on 3D plotting in Matplotlib, see: https://matplotlib.org/stable/gallery/mplot3d/index.html
    """
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

def plot_points(points, color, ax):
    """Plots a list of points in 3D space.

    Args:
        points (list): List of points (x', y', z') to plot.
        color (str): Color of the points.
        ax (Axes3D): The 3D axes to plot on.

    Reference:
    For more details on 3D plotting and transformations, see: https://matplotlib.org/stable/gallery/mplot3d/index.html
    """
    for point in points:
        ax.scatter(*point, color=color, s=10)

def plot_cylinder_with_filled_circle(L, H, R, cylinder_resolution, circle_resolution, circle_radius, circle_height):
    """Plots the cylindrical transformation of a pixelated rectangle with a filled circle on the surface.

    Args:
        L (float): The length of the rectangle.
        H (float): The height of the rectangle.
        R (float): The radius of the cylinder.
        cylinder_resolution (float): The resolution of the pixelation of the cylinder.
        circle_resolution (float): The resolution of the circle filling.
        circle_radius (float): The radius of the circle.
        circle_height (float): The height position of the circle on the cylinder.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    cylinder_points = transform_rectangle_to_cylinder(L, H, R, cylinder_resolution)
    circle_points = transform_circle_to_cylinder(L, R, circle_radius, circle_height, circle_resolution)

    plot_points(cylinder_points, 'r', ax)
    plot_points(circle_points, 'b', ax)

    ax.set_xlim([-R - 1, R + 1])
    ax.set_ylim([-R - 1, R + 1])
    ax.set_zlim([0, H])
    ax.set_title('Cylinder with Filled Circle')
    plt.show()


__all__ = ["plot_cylinder_with_filled_circle"]
