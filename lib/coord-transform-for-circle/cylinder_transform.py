import numpy as np
import plotly.graph_objects as go

# References:
# 1. Cylindrical Coordinates: https://mathinsight.org/cylindrical_coordinates

def transform_to_cylinder(x, y, L, R):
    theta = 2 * np.pi * x / L
    x_prime = R * np.cos(theta)
    y_prime = R * np.sin(theta)
    z_prime = y
    return x_prime, y_prime, z_prime

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

def plot_points(points, color, ax):
    for point in points:
        ax.scatter(*point, color=color, s=10)

def plot_cylinder_with_filled_circle(L, H, R, cylinder_resolution, circle_resolution, circle_radius, circle_height):
    cylinder_points = transform_rectangle_to_cylinder(L, H, R, cylinder_resolution)
    circle_points = transform_circle_to_cylinder(L, R, circle_radius, circle_height, circle_resolution)

    # Create Plotly scatter plot
    fig = go.Figure()

    # Add rectangle points
    fig.add_trace(go.Scatter3d(
        x=cylinder_points[:, 0],
        y=cylinder_points[:, 1],
        z=cylinder_points[:, 2],
        mode='markers',
        marker=dict(size=3, color='red'),
        name='Rectangle'
    ))

    # Add circle points
    fig.add_trace(go.Scatter3d(
        x=circle_points[:, 0],
        y=circle_points[:, 1],
        z=circle_points[:, 2],
        mode='markers',
        marker=dict(size=3, color='blue'),
        name='Circle'
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-R-1, R+1]),
            yaxis=dict(range=[-R-1, R+1]),
            zaxis=dict(range=[0, H]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        title='Cylinder with Filled Circle'
    )
    
    fig.show()



__all__ = ["plot_cylinder_with_filled_circle, transform_rectangle_to_cylinder"]
