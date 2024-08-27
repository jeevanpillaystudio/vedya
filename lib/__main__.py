import click
from matplotlib import pyplot as plt
import numpy as np

from src.render_form import (
    render_3d_plot,
    render_2d_stencil,
)

from src.coord_transform import (
    transform_circle_to_cylinder,
    transform_rectangle_to_cylinder,
)

from src.examples.flow_field_visual import generate_2d_flowfield

"""
# @TODO
- [ ] apply monochromatic color profile to the output; default is grayscale
- [ ] structure app; using pattern -> transform -> render
- [ ] run command as such `vedya transform input.txt --target cylindrical --resolution 0.1 --length 10 --height 4 --radius 1 --output output.txt`
    - [ ] assuming `input.txt` is some x, y bounded cartesian system
    - [ ] output.txt is a set of x, y, z values
- [ ] run command as such `vedya render output.txt --output output.stl --color grayscale`
    - [ ] output.stl is a 3D model of the transformed input
"""


@click.group()
def cli():
    pass


@cli.command("transform")
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path())
@click.option("--target", type=click.Choice(["cylinder", "sphere"]))
def transform(input, output, target):
    # parse the input file
    with open(input, "r") as file:
        for line_number, line in enumerate(file, start=1):
            # Strip whitespace and split the line into values
            values = line.strip().split()

            try:
                # Convert each value to a float
                float_values = [float(value) for value in values]
                print(f"Line {line_number}: {float_values}")
            except ValueError as e:
                # Handle any conversion errors
                print(f"Error parsing line {line_number}: {line.strip()}")
                print(f"Reason: {e}")

    # create output if it doesn't exist
    with open(output, "w") as file:
        file.write("initializing output file")

    if target == "cylinder":
        render_3d_plot(
            coord_points=transform_rectangle_to_cylinder(
                L=10, H=4, R=1, resolution=0.1
            ),
            target_points=transform_circle_to_cylinder(
                L=10, R=1, circle_radius=1, circle_height=2, resolution=0.1
            ),
            R=1,
            H=4,
        )
    elif target == "sphere":
        raise NotImplementedError("sphere transformation is not yet implemented")
    else:
        raise ValueError("invalid target")


@cli.command("render")
@click.argument("input", type=click.Path(exists=True))
@click.option("--post-render", type=click.Choice(["2d-stencil"]))
def render(input, post_render):
    # post-render option
    if post_render == "2d-stencil":
        render_2d_stencil(img_path=input)  # @TODO fix pathing...


@cli.command("example")
@click.argument("output", type=click.Path(exists=False))
def example(output):
    # Parameters
    width = 100
    height = 100
    scale = 0.1
    octaves = 4
    persistence = 0.5
    lacunarity = 2.0

    # Generate and plot the 2D Flowfield
    flow_field = generate_2d_flowfield(
        width, height, scale, octaves, persistence, lacunarity
    )
    plot_2d_flowfield(flow_field)


# @TODO move to render_form plot...
def plot_2d_flowfield(flow_field):
    height, width, _ = flow_field.shape
    x = np.linspace(0, width, width)
    y = np.linspace(0, height, height)
    x, y = np.meshgrid(x, y)

    u = flow_field[:, :, 0]
    v = flow_field[:, :, 1]

    plt.figure(figsize=(10, 10))
    plt.quiver(x, y, u, v, color="blue")
    plt.title("2D Flowfield")
    plt.show()


if __name__ == "__main__":
    cli()
