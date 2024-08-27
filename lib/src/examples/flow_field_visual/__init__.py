import numpy as np
from noise import pnoise2


def generate_2d_flowfield(
    width, height, scale, octaves, persistence, lacunarity
) -> np.ndarray:
    # Create a grid of points
    x = np.linspace(0, width, width)
    y = np.linspace(0, height, height)
    x, y = np.meshgrid(x, y)

    # Initialize the flow field
    flow_field = np.zeros((height, width, 2))

    # Generate Perlin noise-based flow field
    for i in range(height):
        for j in range(width):
            angle = (
                pnoise2(
                    j * scale,
                    i * scale,
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

    return flow_field
