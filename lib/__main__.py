import click

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
def main(input):
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


# @click.option("--output", help="Output file path")
# @click.option(
#     "--target",
#     help="Target coordinate system",
#     type=click.Choice(["cylinder", "sphere"]),
# )
# @click.option(
#     "--resolution",
#     default=0.1,
#     help="Resolution of the target coordinate system",
# )
# @click.option(
#     "--L",
#     help="Length of the target coordinate system",
# )
# @click.option(
#     "--H",
#     help="Height of the target coordinate system",
# )
# @click.option(
#     "--R",
#     help="Radius of the target coordinate system",
# )
# def main(input, output, target, resolution, length, height, radius):
#     if target == "cylinder":
#         print("Cylindrical transformation")
#     elif target == "sphere":
#         print("Spherical transformation")
#     else:
#         print("Unknown target coordinate system")


if __name__ == "__main__":
    main()
