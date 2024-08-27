import plotly.graph_objects as go
from .src.cylinder import (
    transform_circle_to_cylinder,
    transform_rectangle_to_cylinder,
)
from .src.sphere import (
    transform_circle_to_sphere,
    transform_rectangle_to_sphere,
)


def main() -> None:
    # Parameters for the transformation
    L = 10  # Length of the rectangle
    H = 4  # Height of the rectangle
    R = 1  # Radius of the cylinder
    cylinder_resolution = 0.1  # Size of each square in the rectangle
    sphere_resolution = 0.1  # Size of each square in the sphere
    circle_resolution = 0.1  # Size of each square in the circle
    circle_radius = 1  # Radius of the circle
    circle_height = 2  # Height position of the circle on the cylinder

    # Plot the cylinder with a filled circle
    plot_cylinder_with_filled_circle(
        L, H, R, cylinder_resolution, circle_resolution, circle_radius, circle_height
    )

    # Plot the sphere with a filled circle
    # plot_sphere_with_filled_circle(L, H, R, sphere_resolution, circle_resolution, circle_radius, circle_height)

    # OpenSCAD model generation
    # create_cylinder_scad_model(L, H, R, cylinder_resolution)


def plot_cylinder_with_filled_circle(
    L, H, R, cylinder_resolution, circle_resolution, circle_radius, circle_height
):
    cylinder_points = transform_rectangle_to_cylinder(L, H, R, cylinder_resolution)
    circle_points = transform_circle_to_cylinder(
        L, R, circle_radius, circle_height, circle_resolution
    )

    # Create Plotly scatter plot
    fig = go.Figure()

    # Add rectangle points
    fig.add_trace(
        go.Scatter3d(
            x=cylinder_points[:, 0],
            y=cylinder_points[:, 1],
            z=cylinder_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="red"),
            name="Rectangle",
        )
    )

    # Add circle points
    fig.add_trace(
        go.Scatter3d(
            x=circle_points[:, 0],
            y=circle_points[:, 1],
            z=circle_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="blue"),
            name="Circle",
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-R - 1, R + 1]),
            yaxis=dict(range=[-R - 1, R + 1]),
            zaxis=dict(range=[0, H]),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=1),
        ),
        title="Cylinder with Filled Circle",
    )

    fig.show()


def plot_sphere_with_filled_circle(
    L, H, R, sphere_resolution, circle_resolution, circle_radius, circle_height
):
    sphere_points = transform_rectangle_to_sphere(L, H, R, sphere_resolution)
    circle_points = transform_circle_to_sphere(
        L, H, R, circle_radius, circle_height, circle_resolution
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=sphere_points[:, 0],
            y=sphere_points[:, 1],
            z=sphere_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="red"),
            name="Rectangle",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=circle_points[:, 0],
            y=circle_points[:, 1],
            z=circle_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="blue"),
            name="Circle",
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-R - 1, R + 1]),
            yaxis=dict(range=[-R - 1, R + 1]),
            zaxis=dict(range=[-R - 1, R + 1]),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=1),
        ),
        title="Sphere with Filled Circle",
    )

    fig.show()


if __name__ == "__main__":
    main()
