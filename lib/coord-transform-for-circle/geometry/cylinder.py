# References:
# 1. Cylindrical Coordinates: https://mathinsight.org/cylindrical_coordinates

import numpy as np


def transform_to_cylinder(x, y, L, R):
    theta = 2 * np.pi * x / L
    x_prime = R * np.cos(theta)
    y_prime = R * np.sin(theta)
    z_prime = y
    return x_prime, y_prime, z_prime


def transform_rectangle_to_cylinder(L, H, R, resolution):
    x_steps = int(L / resolution)
    y_steps = int(H / resolution)

    points = []
    for i in range(x_steps):
        for j in range(y_steps):
            x = i * resolution + resolution / 2
            y = j * resolution + resolution / 2
            x_prime, y_prime, z_prime = transform_to_cylinder(x, y, L, R)
            points.append((x_prime, y_prime, z_prime))

    return np.array(points)


def transform_circle_to_cylinder(L, R, circle_radius, circle_height, resolution):
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

    return np.array(points)
