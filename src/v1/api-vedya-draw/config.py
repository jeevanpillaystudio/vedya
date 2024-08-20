# class AstroidConfig:
#     def __init__(self):
#         pass

#     def __str__(self) -> str:
#         return f"AstroidConfig: NumPoints={self.NumPoints}, N={self.N}, OuterAstroidRadius={self.OuterAstroidRadius}, InnerAstroidRadius={self.InnerAstroidRadius}"

#     N = 2 / 3
#     NumPoints = 128

#     OuterAstroidRadius = (32.0 - 2.56) * ScaleConfig.ScaleFactor
#     OuterAstroidStrokeWeight = AppConfig.StrokeWeight * ScaleConfig.ScaleFactor

#     InnerAstroidRadius = (16.0 + 2.56) * ScaleConfig.ScaleFactor
#     InnerAstroidStrokeWeight = AppConfig.StrokeWeight * ScaleConfig.ScaleFactor


# class KailashConfig:
#     def __init__(self):
#         pass

#     # KailashIntersectExtrudeArea = 2130.679120238867 * ScaleConfig.ScaleFactor ** 2 # this is the area of the intersected extrusion of the kailash terrain, manually created. @todo - automate this
#     KailashIntersectExtrudeArea = 401.66169829603086
#     AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea = 1.2765358608164958
#     OuterDiagonalCutWithAstroidExtrudeArea = 12.375340707128288


# class SeedOfLifeConfig:
#     def __init__(self):
#         pass

#     MinRandomMultiple = 1
#     MaxRandomMultiple = 1
#     # DepthRepeatValues = create_power_series_multiples(3) # the values of the iterator repeat can only be either 1, 2 or 4 times; e.g [1, 2, 4]
#     DepthRepeatValues = [1]

#     AngleDifference = 30

#     StrokeWeight = 0.64 * ScaleConfig.ScaleFactor


# def create_middle_cut(root_comp):
#     try:
#         middle_circle_comp = create_component(
#             component=root_comp,
#             name=create_component_name("middle_circle_comp"),
#         )

#         sketch = create_sketch(
#             middle_circle_comp, "hole-thin-circle", offset=AppConfig.LayerDepth
#         )
#         stroke_weight = AppConfig.LayerDepth * 1.5 * ScaleConfig.ScaleFactor
#         draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
#         extrude_thin_one(
#             component=middle_circle_comp,
#             profile=sketch.profiles[0],
#             extrudeHeight=AppConfig.LayerDepth * 6,
#             strokeWeight=stroke_weight,
#             name="hole-thin-circle",
#             operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             side=DepthEffect.Side2,
#         )

#         sketch = create_sketch(middle_circle_comp, "cut-hole", offset=0.0)
#         draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
#         extrude_profile_by_area(
#             component=middle_circle_comp,
#             profiles=sketch.profiles,
#             area=calculate_circle_area(AppConfig.HoleRadius),
#             extrude_height=AppConfig.LayerDepth * 9,
#             name="cut-hole",
#             operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
#         )
#     except:
#         log("cut-hole: none to cut")


# def create_torus_astroid(root_comp):
#     if not component_exist(root_comp, create_component_name("torus")):
#         torus_comp = create_component(
#             component=root_comp, name=create_component_name("torus")
#         )

#         # inner torus
#         iterations = 16
#         radius = random.choice([0.48 * 20 * 2]) * ScaleConfig.ScaleFactor
#         stroke_weight = random.choice([0.32]) * ScaleConfig.ScaleFactor
#         inner_torus_component = create_component(
#             component=torus_comp,
#             name=create_component_name(
#                 "torus-outer-" + str(radius) + "-" + str(iterations)
#             ),
#         )
#         depth_repeat = 2
#         start_layer_offset = AppConfig.LayerDepth * 6
#         extrude_height_per_layer = AppConfig.LayerDepth / depth_repeat

#         for layer_offset, sw in depth_repeat_iterator(
#             depth_repeat,
#             start_layer_offset,
#             extrude_height_per_layer,
#             stroke_weight,
#             direction=DepthRepeat.Decrement,
#         ):
#             # create the torus
#             torus_layer_0_inner_comp = create_component(
#                 component=inner_torus_component,
#                 name=create_component_name(
#                     "torus-inner-" + str(radius) + "-" + str(sw)
#                 ),
#             )
#             create_torus(
#                 component=torus_layer_0_inner_comp,
#                 center_x=0,
#                 center_y=0,
#                 radius=radius,
#                 iterations=iterations,
#                 stroke_weight=sw,
#                 extrude_height=extrude_height_per_layer,
#                 layer_offset=layer_offset,
#             )

#             # get all bodies
#             invert_bodies = adsk.core.ObjectCollection.create()
#             for body in torus_layer_0_inner_comp.bRepBodies:
#                 invert_bodies.add(body)

#             # invert the joint body; re should always be in first occurance
#             sketch = create_sketch(
#                 torus_comp, "torus-astroid-32-inverse", offset=layer_offset
#             )
#             draw_astroid(
#                 sketch=sketch,
#                 n=AstroidConfig.N,
#                 numPoints=AstroidConfig.NumPoints,
#                 scaleX=AstroidConfig.InnerAstroidRadius
#                 - AstroidConfig.InnerAstroidStrokeWeight,
#                 scaleY=AstroidConfig.InnerAstroidRadius
#                 - AstroidConfig.InnerAstroidStrokeWeight,
#             )
#             invert_body = extrude_single_profile_by_area(
#                 component=torus_comp,
#                 profiles=sketch.profiles,
#                 area=calculate_astroid_area(
#                     AstroidConfig.InnerAstroidRadius
#                     - AstroidConfig.InnerAstroidStrokeWeight
#                 ),
#                 extrude_height=extrude_height_per_layer,
#                 name="astroid-32-inner",
#                 fp_tolerance=1e-0,
#             )
#             combine_body(
#                 torus_comp,
#                 invert_body,
#                 invert_bodies,
#                 operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
#             )

#             # add astroid bracing (stroke)
#             sketch = create_sketch(
#                 torus_comp, "torus-astroid-32-inverse-bracing", offset=layer_offset
#             )
#             draw_astroid_stroke(
#                 sketch=sketch,
#                 n=AstroidConfig.N,
#                 numPoints=AstroidConfig.NumPoints,
#                 scaleX=AstroidConfig.InnerAstroidRadius
#                 - AstroidConfig.InnerAstroidStrokeWeight,
#                 scaleY=AstroidConfig.InnerAstroidRadius
#                 - AstroidConfig.InnerAstroidStrokeWeight,
#                 strokeWeight=AppConfig.StrokeWeight,
#             )
#             extrude_profile_by_area(
#                 component=torus_comp,
#                 profiles=sketch.profiles,
#                 area=calculate_astroid_area(
#                     AstroidConfig.InnerAstroidRadius
#                     - AstroidConfig.InnerAstroidStrokeWeight
#                 )
#                 - calculate_astroid_area(
#                     AstroidConfig.InnerAstroidRadius
#                     - AstroidConfig.InnerAstroidStrokeWeight
#                     - AppConfig.StrokeWeight
#                 ),
#                 extrude_height=extrude_height_per_layer,
#                 name="torus-astroid-bracing",
#                 operation=adsk.fusion.FeatureOperations.JoinFeatureOperation,
#                 fp_tolerance=1e-0,
#             )

#         # combine all the bodies
#         all_bodies = aggregate_all_bodies(torus_comp)
#         root_body = all_bodies.item(0)
#         all_bodies.removeByIndex(0)
#         combine_body(
#             torus_comp,
#             root_body,
#             all_bodies,
#             operation=adsk.fusion.FeatureOperations.JoinFeatureOperation,
#         )


# def create_component_outer_diagonal_steps(root_comp: adsk.fusion.Component):
#     if not component_exist(
#         root_comp, create_component_name("interstellar-tesellation")
#     ):
#         interstellar_tesellation_comp = create_component(
#             component=root_comp,
#             name=create_component_name("interstellar-tesellation"),
#         )

#         # draw from middle
#         center_x = 0
#         center_y = 0
#         depth_repeat = 4
#         extrude_height_per_layer = AppConfig.LayerDepth * 2 / depth_repeat
#         stroke_weight = 0.72 * ScaleConfig.ScaleFactor
#         start_layer_offset = AppConfig.LayerDepth * 3

#         for layer_offset, sw in depth_repeat_iterator(
#             depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight
#         ):
#             sketch = create_sketch(
#                 interstellar_tesellation_comp,
#                 "interstellar-tesellation-outer",
#                 offset=layer_offset,
#             )
#             draw_rotated_rectangle(
#                 sketch=sketch,
#                 width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
#                 height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
#             )
#             extrude_thin_one(
#                 component=interstellar_tesellation_comp,
#                 profile=sketch.profiles[0],
#                 extrudeHeight=extrude_height_per_layer,
#                 strokeWeight=sw,
#                 name="interstellar-tesellation-outer",
#                 operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             )

#         # for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight):
#         #     sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-middle', offset=layer_offset)
#         #     draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
#         #     extrude_thin_one(component=interstellar_tesellation_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='interstellar-tesellation-middle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side2)

#         # cut with AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea
#         # sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-astroid-outer-cut', offset=AppConfig.LayerDepth)
#         # draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
#         # draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
#         # extrude_profile_y_area(component=interstellar_tesellation_comp, profiles=sketch.profiles, area=KailashConfig.AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea, extrude_height=AppConfig.LayerDepth, name='interstellar-tesellation-astroid-outer-cut', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)


# def create_component_core(root_comp):
#     if not component_exist(root_comp, create_component_name("core")):
#         main_comp = create_component(
#             component=root_comp, name=create_component_name("core")
#         )

#         # level 2D -----------
#         layer_offset = AppConfig.LayerDepth * 2

#         # draw the bottom layer diagonal
#         sketch = create_sketch(main_comp, "seed-of-life-base", offset=layer_offset)
#         extrude_height = AppConfig.LayerDepth * 2
#         draw_rectangle(
#             sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
#         )
#         draw_rotated_rectangle(
#             sketch=sketch,
#             width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
#             height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
#         )
#         extrude_single_profile_by_area(
#             component=main_comp,
#             profiles=sketch.profiles,
#             area=calculate_rectangle_area(AppConfig.MaxWidth, AppConfig.MaxLength)
#             - calculate_three_point_rectangle_area(
#                 DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
#                 DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
#             ),
#             extrude_height=extrude_height,
#             name="seed-of-life-base",
#             operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#         )

#         # level 2.5D -----------

#         # nothing....

#         # level 2.5 -----------
#         layer_offset = AppConfig.LayerDepth * 2.5

#         # draw the rotated rectangle middle
#         sketch = create_sketch(
#             main_comp, "angled-rectangles-middle", offset=layer_offset
#         )
#         extrude_height = AppConfig.LayerDepth * 3
#         draw_rotated_rectangle(
#             sketch=sketch,
#             width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
#             height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
#         )
#         for profile in sketch.profiles:
#             extrude_thin_one(
#                 component=main_comp,
#                 profile=profile,
#                 extrudeHeight=extrude_height,
#                 strokeWeight=DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight,
#                 name="angled-rectangles-middle",
#                 operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             )

#         # draw the astroid 64
#         sketch = create_sketch(main_comp, "astroid-64-outer", offset=layer_offset)
#         extrude_height = AppConfig.LayerDepth
#         draw_astroid(
#             sketch=sketch,
#             n=AstroidConfig.N,
#             numPoints=AstroidConfig.NumPoints,
#             scaleX=AstroidConfig.OuterAstroidRadius,
#             scaleY=AstroidConfig.OuterAstroidRadius,
#         )
#         extrude_profile_by_area(
#             component=main_comp,
#             profiles=sketch.profiles,
#             area=calculate_astroid_area(AstroidConfig.OuterAstroidRadius),
#             extrude_height=extrude_height,
#             name="astroid-64-outer",
#             fp_tolerance=1e0,
#         )

#         # level 3D -----------
#         layer_offset = AppConfig.LayerDepth * 3

#         # draw the astroid 64 inner
#         sketch = create_sketch(main_comp, "astroid-64-inner", offset=layer_offset)
#         extrude_height = AppConfig.LayerDepth * 2
#         draw_astroid(
#             sketch=sketch,
#             n=AstroidConfig.N,
#             numPoints=AstroidConfig.NumPoints,
#             scaleX=AstroidConfig.OuterAstroidRadius
#             - AstroidConfig.OuterAstroidStrokeWeight,
#             scaleY=AstroidConfig.OuterAstroidRadius
#             - AstroidConfig.OuterAstroidStrokeWeight,
#         )
#         extrude_profile_by_area(
#             component=main_comp,
#             profiles=sketch.profiles,
#             area=calculate_astroid_area(
#                 AstroidConfig.OuterAstroidRadius
#                 - AstroidConfig.OuterAstroidStrokeWeight
#             ),
#             extrude_height=extrude_height,
#             name="astroid-64-inner",
#             fp_tolerance=1e0,
#         )

#         # level 5D -----------
#         layer_offset = AppConfig.LayerDepth * 5

#         # draw the rotated rectangle inner
#         sketch = create_sketch(
#             main_comp, "angled-rectangles-inner", offset=layer_offset
#         )
#         extrude_height = AppConfig.LayerDepth * 2
#         draw_rotated_rectangle(
#             sketch=sketch,
#             width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth,
#             height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight,
#         )
#         for profile in sketch.profiles:
#             extrude_thin_one(
#                 component=main_comp,
#                 profile=profile,
#                 extrudeHeight=extrude_height,
#                 strokeWeight=DiagonalRectangleConfig.InnerDiagonalRectangleStrokeWeight,
#                 name="angled-rectangles-inner",
#                 operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             )

#             # draw the astroid 32
#         sketch = create_sketch(main_comp, "astroid-32-outer", offset=layer_offset)
#         extrude_height = AppConfig.LayerDepth
#         draw_astroid(
#             sketch=sketch,
#             n=AstroidConfig.N,
#             numPoints=AstroidConfig.NumPoints,
#             scaleX=AstroidConfig.InnerAstroidRadius,
#             scaleY=AstroidConfig.InnerAstroidRadius,
#         )
#         extrude_profile_by_area(
#             component=main_comp,
#             profiles=sketch.profiles,
#             area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius),
#             extrude_height=extrude_height,
#             name="astroid-32-outer",
#             fp_tolerance=1e0,
#         )

#         # layer 6D -----------
#         layer_offset = AppConfig.LayerDepth * 6

#         # draw the astroid 32 inner
#         sketch = create_sketch(main_comp, "astroid-32-inner", offset=layer_offset)
#         extrude_height = AppConfig.LayerDepth
#         draw_astroid(
#             sketch=sketch,
#             n=AstroidConfig.N,
#             numPoints=AstroidConfig.NumPoints,
#             scaleX=AstroidConfig.InnerAstroidRadius
#             - AstroidConfig.InnerAstroidStrokeWeight,
#             scaleY=AstroidConfig.InnerAstroidRadius
#             - AstroidConfig.InnerAstroidStrokeWeight,
#         )
#         extrude_profile_by_area(
#             component=main_comp,
#             profiles=sketch.profiles,
#             area=calculate_astroid_area(
#                 AstroidConfig.InnerAstroidRadius
#                 - AstroidConfig.InnerAstroidStrokeWeight
#             ),
#             extrude_height=extrude_height,
#             name="astroid-32-inner",
#             fp_tolerance=1e0,
#         )


# @timer
# def slicer(
#     component: adsk.fusion.Component,
#     design: adsk.core.Product,
#     sliced_layer_depth: float,
#     sliced_layer_count: float,
# ):
#     # Ensure design is set to parametric
#     design.designType = adsk.fusion.DesignTypes.ParametricDesignType

#     # Create a new component for the slicing operation
#     slicer_comp = create_component(component, create_component_name("slicer"))

#     # Gather all bodies from the root component and its subcomponents
#     all_bodies = aggregate_all_bodies(component)

#     # Combine the rest of the bodies with the main body
#     tool_bodies = adsk.core.ObjectCollection.create()
#     for i in range(all_bodies.count):
#         body_copy = copy_body(slicer_comp, all_bodies.item(i), "slicer-body-" + str(i))
#         tool_bodies.add(body_copy)

#     # Perform the combination
#     first_body = tool_bodies.item(0)
#     tool_bodies.removeByIndex(0)
#     combine_body(
#         slicer_comp,
#         first_body,
#         tool_bodies,
#         adsk.fusion.FeatureOperations.JoinFeatureOperation,
#     )

#     # rename
#     first_body.name = "slicer-body-root"

#     # slice the body
#     slice_body(slicer_comp, first_body, sliced_layer_depth, sliced_layer_count)


# def aggregate_all_bodies(
#     component: adsk.fusion.Component,
#     all_bodies: adsk.core.ObjectCollection = None,
#     depth_limit: int = -1,
# ):
#     if all_bodies is None:
#         all_bodies = adsk.core.ObjectCollection.create()

#     # Add all bodies from the current component
#     for body in component.bRepBodies:
#         all_bodies.add(body)

#     # Check if the depth limit has been reached
#     if depth_limit == 0:
#         return all_bodies

#     # Recursively process all subcomponents, decreasing depth limit by 1 with each call
#     for occurrence in component.occurrences:
#         aggregate_all_bodies(
#             occurrence.component, all_bodies, depth_limit - 1 if depth_limit > 0 else -1
#         )

#     return all_bodies


# @timer
# def slice_body(
#     slicer_component: adsk.fusion.Component,
#     body: adsk.fusion.BRepBody,
#     sliced_layer_depth: float,
#     sliced_layer_count: float,
# ):
#     log(
#         f"slice_body: body: {body.name}, sliced_layer_depth: {sliced_layer_depth}, sliced_layer_count: {sliced_layer_count}"
#     )

#     # Get the bounding box of the body
#     bounding_box = body.boundingBox
#     min_point = bounding_box.minPoint
#     max_point = bounding_box.maxPoint

#     # Calculate the dimensions
#     height = max_point.z - min_point.z

#     # Calculate the number of slices and the height of each slice
#     slice_height = sliced_layer_depth
#     slice_count = int(min(sliced_layer_count, math.floor(height / slice_height)))

#     # Log the details (assumed log function exists or use print instead)
#     print(
#         f"slice_body: height: {height}, slice_count: {slice_count}, slice_height: {slice_height}"
#     )

#     # Iterate to create each slice
#     for i in range(slice_count):
#         # Calculate the offset for the current plane
#         offset = min_point.z + ((i + 1) * slice_height)

#         # Create an offset plane at the calculated position
#         offset_plane = create_offset_plane(
#             slicer_component, offset, name=f"plane-slice-{i}"
#         )

#         # log
#         log(f"slice_body: offset_plane: {offset_plane.name}, offset: {offset}")

#         # Split the body using the created plane

#         split_body_features = slicer_component.features.splitBodyFeatures
#         split_body_input = split_body_features.createInput(body, offset_plane, True)
#         newBodies = split_body_features.add(split_body_input).bodies

#         # Get the new body
#         slice_body = newBodies.item(0)
#         slice_body.name = f"slice-body-{i}"

#         # replace the original body with the new body
#         body = newBodies.item(1)
#         body.name = f"slice-body-remaining"


# @timer
# def create_torus(
#     component: adsk.fusion.Component,
#     center_x,
#     center_y,
#     radius,
#     iterations,
#     stroke_weight,
#     extrude_height,
#     layer_offset,
# ):
#     sketch = create_sketch(
#         component,
#         "torus-outer-circle-" + str(radius) + "-" + str(iterations),
#         offset=layer_offset,
#     )

#     # draw the outer circle
#     draw_circle(sketch, radius, center_x, center_y)
#     initial_body = extrude_thin_one(
#         component=component,
#         profile=sketch.profiles[0],
#         extrudeHeight=extrude_height,
#         strokeWeight=stroke_weight,
#         name="torus-outer-circle" + str(radius) + "-" + str(iterations),
#         operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#     )
#     initial_body.name = "torus-outer-circle" + str(radius) + "-" + str(iterations)

#     # draw throwaway circle (remove at the end) with scale non-uniform; x, y = 0.5
#     if AppConfig.DesignMode == DesignMode.DirectDesign:
#         pass
#     elif AppConfig.DesignMode == DesignMode.ParametricDesign:
#         throwaway_body = copy_body(
#             component,
#             initial_body,
#             name="torus-outer-circle-throwaway-" + str(radius) + "-" + str(iterations),
#         )
#         scale_body(
#             component=component,
#             body=throwaway_body,
#             scale_x=0.5,
#             scale_y=0.5,
#             scale_z=1,
#             sketch_pt=sketch.sketchPoints.item(0),
#         )
#     else:
#         raise Exception("DesignMode not supported")

#     # create the torus
#     angle_per_iteration = 360 / iterations
#     r = radius / 2.0

#     # draw; this is a standard torus algorithm.
#     for i in range(iterations):
#         # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
#         angle = math.radians(i * angle_per_iteration)
#         x = center_x + r * math.cos(angle)
#         y = center_y + r * math.sin(angle)

#         # draw
#         if AppConfig.DesignMode == DesignMode.DirectDesign:
#             real_sketch = create_sketch(
#                 component,
#                 "torus-inner-circle-" + str(r) + "-" + str(angle),
#                 layer_offset,
#             )
#             draw_circle(real_sketch, r, x, y)
#             extrude_thin_one(
#                 component=component,
#                 profile=real_sketch.profiles[0],
#                 extrudeHeight=extrude_height,
#                 strokeWeight=stroke_weight,
#                 name="torus-inner-circle-" + str(r) + "-" + str(angle),
#                 operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             )
#         elif AppConfig.DesignMode == DesignMode.ParametricDesign:
#             real_body = copy_body(
#                 component=component,
#                 body=throwaway_body,
#                 name="torus-inner-circle-" + str(r) + "-" + str(angle),
#             )
#             move_body(component, x, y, real_body)
#         else:
#             raise Exception("DesignMode not supported")

#     # log the seed of life
#     log(f"torus: {iterations} circles with radius: {r}")
