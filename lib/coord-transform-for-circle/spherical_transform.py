import numpy as np
import plotly.graph_objects as go

def transform_to_spherical(x, y, L, H, R):
    theta = 2 * np.pi * x / L  # Map x to theta (0 to 2pi)
    phi = np.pi * y / H        # Map y to phi (0 to pi)
    x_prime = R * np.sin(phi) * np.cos(theta)
    y_prime = R * np.sin(phi) * np.sin(theta)
    z_prime = R * np.cos(phi)
    return x_prime, y_prime, z_prime

def transform_circle_to_spherical(L, H, R, circle_radius, circle_height, resolution):
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
            x_prime, y_prime, z_prime = transform_to_spherical(x, y, L, H, R)
            points.append((x_prime, y_prime, z_prime))

    return np.array(points)

def transform_rectangle_to_spherical(L, H, R, resolution):
    x_steps = int(L / resolution)
    y_steps = int(H / resolution)

    points = []
    for i in range(x_steps):
        for j in range(y_steps):
            x = i * resolution + resolution / 2
            y = j * resolution + resolution / 2
            x_prime, y_prime, z_prime = transform_to_spherical(x, y, L, H, R)
            points.append((x_prime, y_prime, z_prime))

    return np.array(points)

def plot_sphere_with_filled_circle(L, H, R, sphere_resolution, circle_resolution, circle_radius, circle_height):
    sphere_points = transform_rectangle_to_spherical(L, H, R, sphere_resolution)
    circle_points = transform_circle_to_spherical(L, H, R, circle_radius, circle_height, circle_resolution)

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=sphere_points[:, 0],
        y=sphere_points[:, 1],
        z=sphere_points[:, 2],
        mode='markers',
        marker=dict(size=3, color='red'),
        name='Rectangle'
    ))

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
            zaxis=dict(range=[-R-1, R+1]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        title='Sphere with Filled Circle'
    )

    fig.show()

__all__ = ["plot_sphere_with_filled_circle"]
