# control

pattern -> transform -> render

pattern -> [input (np.arrray of values) -> coord-transform -> output (np.array of values)] -> [post-process (e.g color profile) -> output (np.array of values)] [input (np.array of coord + color) render -> output (e.g. stl, obj, png (types: stencil/etc))] 

1. work within transformations of cartesian to either spherical or cylindrical coordinates.
    - [ ] @TODO implement spherical to cartesian
    - [ ] @TODO implement cylindrical to cartesian


# @TODO
- [ ] apply monochromatic color profile to the output; default is grayscale
- [ ] structure app; using pattern -> transform -> render
- [ ] run command as such `vedya transform input.txt --target cylindrical --resolution 0.1 --length 10 --height 4 --radius 1 --output output.txt`
    - [ ] assuming `input.txt` is some x, y bounded cartesian system
    - [ ] output.txt is a set of x, y, z values
- [ ] run command as such `vedya render output.txt --output output.stl --color grayscale`
    - [ ] output.stl is a 3D model of the transformed input


# # Parameters for the transformation
# L = 10  # Length of the rectangle
# H = 4  # Height of the rectangle
# R = 1  # Radius of the cylinder
# cylinder_resolution = 0.1  # Size of each square in the rectangle
# sphere_resolution = 0.1  # Size of each square in the sphere
# circle_resolution = 0.1  # Size of each square in the circle
# circle_radius = 1  # Radius of the circle
# circle_height = 2  # Height position of the circle on the cylinder