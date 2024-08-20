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
