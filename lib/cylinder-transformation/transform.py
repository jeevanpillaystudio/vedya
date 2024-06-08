"""transformation of shapes to cylinder coordinate system"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def transform_to_cylinder(x, y, L, H, R):
    """Transforms a single point (x, y) on the rectangle into cylindrical coordinates."""
    theta = 2 * np.pi * x / L
    x_prime = R * np.cos(theta)
    y_prime = R * np.sin(theta)
    z_prime = y
    return x_prime, y_prime, z_prime


def plot_cylinder_with_circle(L, H, R, cylinder_resolution, circle_resolution,
                              circle_radius, circle_height):
    """Plots the cylindrical transformation of a pixelated rectangle with a circle on the surface."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Calculate the number of steps based on resolution
    x_steps = int(L / cylinder_resolution)
    y_steps = int(H / cylinder_resolution)

    # Create the cylinder
    for i in range(x_steps):
        for j in range(y_steps):
            x = i * cylinder_resolution + cylinder_resolution / 2  # Center of the pixel
            y = j * cylinder_resolution + cylinder_resolution / 2
            x_prime, y_prime, z_prime = transform_to_cylinder(x, y, L, H, R)
            ax.scatter(x_prime, y_prime, z_prime, color='r',
                       s=10)  # Plot each pixel as a point

        # Create a filled circle on the cylinder
        for j in range(int(2 * circle_radius / circle_resolution)):
            for k in range(int(2 * np.pi * circle_radius / circle_resolution)):
                r = circle_radius * (j * circle_resolution /
                                     (2 * circle_radius))  # Radius fraction
                theta = 2 * np.pi * k / int(
                    2 * np.pi * circle_radius / circle_resolution)
                x = r * np.cos(theta)
                y = circle_height + r * np.sin(theta)
                z = circle_height + r * np.cos(theta)
                x_prime, y_prime, z_prime = transform_to_cylinder(
                    x, y, L, H, R)
                ax.scatter(x_prime, y_prime, z_prime, color='b', s=10)

    ax.set_xlim([-R - 1, R + 1])
    ax.set_ylim([-R - 1, R + 1])
    ax.set_zlim([0, H])
    ax.set_title('Cylinder with Circle')
    plt.show()


# Parameters for the transformation
# L = 10  # Length of the rectangle
# H = 5  # Height of the rectangle
# R = 1  # Radius of the cylinder
# cylinder_resolution = 0.4  # Size of each square in the rectangle
# circle_resolution = 0.2  # Size of each square in the circle
# circle_radius = 1.2  # Radius of the circle
# circle_height = 2.5  # Height position of the circle on the cylinder

# Plot the cylinder with a circle
# plot_cylinder_with_circle(L, H, R, cylinder_resolution, circle_resolution,
#                         circle_radius, circle_height)

__all__ = ["plot_cylinder_with_circle"]
