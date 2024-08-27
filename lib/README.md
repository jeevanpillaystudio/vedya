# control

pattern -> transform -> render

pattern -> [input (np.arrray of values) -> coord-transform -> output (np.array of values)] -> [post-process (e.g color profile) -> output (np.array of values)] [input (np.array of coord + color) render -> output (e.g. stl, obj, png (types: stencil/etc))] 

1. work within transformations of cartesian to either spherical or cylindrical coordinates.
    - [ ] @TODO implement spherical to cartesian
    - [ ] @TODO implement cylindrical to cartesian


# @TODO
- [ ] apply monochromatic color profile to the output; default is grayscale
- [ ] structure app; using pattern -> transform -> render