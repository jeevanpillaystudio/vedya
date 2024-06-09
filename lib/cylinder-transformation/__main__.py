"""An example main Python module."""

import sys

from . import plot_cylinder_with_filled_circle 


def main() -> None:
    # Parameters for the transformation
    L = 10  # Length of the rectangle
    H = 4  # Height of the rectangle
    R = 1  # Radius of the cylinder
    cylinder_resolution = 0.4  # Size of each square in the rectangle
    circle_resolution = 0.1  # Size of each square in the circle
    circle_radius = 1.2  # Radius of the circle
    circle_height = 2.5  # Height position of the circle on the cylinder

    # Plot the cylinder with a filled circle
    plot_cylinder_with_filled_circle(L, H, R, cylinder_resolution, circle_resolution, circle_radius, circle_height)

if __name__ == "__main__":
    main()
