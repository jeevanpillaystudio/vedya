import numpy as np
import matplotlib.pyplot as plt
import noise
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def generate_flow_field(
    width=150, height=150, scale=0.1, octaves=6, persistence=0.5, lacunarity=2.0
):
    # Create grid
    x = np.linspace(0, 5, width)
    y = np.linspace(0, 5, height)
    x, y = np.meshgrid(x, y)

    # Generate Perlin noise-based flow field
    flow_field = np.zeros((height, width, 2))
    angles = np.zeros((height, width))

    for i in range(height):
        for j in range(width):
            angle = (
                noise.pnoise2(
                    x[i, j] * scale,
                    y[i, j] * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=width,
                    repeaty=height,
                    base=0,
                )
                * 2
                * np.pi
            )
            flow_field[i, j] = [np.cos(angle), np.sin(angle)]
            angles[i, j] = angle

    # Create color map based on angles
    normalized_angles = (angles + np.pi) / (2 * np.pi)  # Normalize angles to [0, 1]
    colors = plt.cm.viridis(normalized_angles)  # Apply colormap

    return x, y, flow_field, colors


def plot_flow_field_on_cube(ax, x, y, flow_field, colors):
    # Define vertices of a cube
    vertices = [
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 1, 1],
    ]

    # Define the 6 faces of the cube
    faces = [
        [vertices[j] for j in [0, 1, 2, 3]],
        [vertices[j] for j in [4, 5, 6, 7]],
        [vertices[j] for j in [0, 1, 5, 4]],
        [vertices[j] for j in [2, 3, 7, 6]],
        [vertices[j] for j in [0, 3, 7, 4]],
        [vertices[j] for j in [1, 2, 6, 5]],
    ]

    # Create a Poly3DCollection for the cube
    cube = Poly3DCollection(faces, linewidths=1, edgecolors="k", alpha=0.1)
    ax.add_collection3d(cube)

    # Map the flow field vectors onto the surface of the cube
    for i in range(len(x)):  # Iterate over the x-dimension of the grid
        for j in range(len(y)):  # Iterate over the y-dimension of the grid
            ax.quiver(
                x[i, j],  # X-coordinate of the vector's starting point
                y[i, j],  # Y-coordinate of the vector's starting point
                0,  # Z-coordinate of the vector's starting point (on the surface of the cube)
                flow_field[i, j, 0],  # X-component of the vector
                flow_field[i, j, 1],  # Y-component of the vector
                0,  # Z-component of the vector (no Z-component since it's on the surface)
                color=colors[i, j],  # Color of the vector based on the angle
                length=0.1,  # Length of the vector
                alpha=0.75,  # Transparency of the vector
            )


# Create a single 3D plot
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection="3d")

# Parameters for the design
scale = 0.1
octaves = 6
persistence = 0.5
lacunarity = 2.0

# Generate the flow field
x, y, flow_field, colors = generate_flow_field(
    scale=scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity
)

# Plot the flow field on the cube
plot_flow_field_on_cube(ax, x, y, flow_field, colors)

# Set the initial viewing angle to simulate a top-down orthographic view
ax.view_init(elev=30, azim=30)  # Adjust elev and azim for different angles

plt.show()
