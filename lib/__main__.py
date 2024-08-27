import click

from render_form import render_plot
from coord_transform import (
    transform_circle_to_cylinder,
    transform_rectangle_to_cylinder,
)

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


@click.command()
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path())
@click.option("--target", type=click.Choice(["cylinder"]))
def main(input, output, target):
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
        render_plot(
            coord_points=transform_rectangle_to_cylinder(
                L=10, H=4, R=1, resolution=0.1
            ),
            target_points=transform_circle_to_cylinder(
                L=10, R=1, circle_radius=1, circle_height=2, resolution=0.1
            ),
            R=1,
            H=4,
        )


if __name__ == "__main__":
    main()
