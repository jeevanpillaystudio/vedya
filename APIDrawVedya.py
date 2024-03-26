import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .shapes import draw_astroid, draw_astroid_stroke, calculate_astroid_area, draw_circle, calculate_circle_area, calculate_rectangle_area, draw_rectangle, draw_rotated_rectangle, calculate_three_point_rectangle_area, draw_seed_of_life_pattern
from .utils import create_offset_plane, create_sketch, extrude_profile_by_area, component_exist, create_component

# structurally
# 1 layer; each having 4 sub-layers
# 1 sub-layer == 0.32cm
# 1 layer == 1.28cm
# total layers = 4
# total depth = 5.12cm
# base = 6.4cm - 5.12cm = 1.28cm

class AppConfig():
    """
    List of the configurations for the creation
    """
    def __init__(self):
        pass
    HoleRadius = 8.0
    Extrude = True
    MaxWidth = 128.0
    MaxLength = 128.0
    LayerDepth = 1.28
    
class AstroidConfig():
    def __init__(self):
        pass
    N = 2/3
    NumPoints = 128

def run(context):
    ui = None
    try:
        # Get the application and root component
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        
        # Check if the design is not in "Design" mode.
        if not design:
            ui.messageBox('It is not supported in current workspace, please switch to DESIGN workspace and try again.')
            return

        # Get the root component of the active design
        root_comp: adsk.fusion.Component = design.rootComponent
        
        # Structural Component - Background
        if not component_exist(root_comp, 'bg'):
            core_structural_comp = create_component(root_component=root_comp, name="bg")
            sketch = create_sketch(core_structural_comp, 'bg-rect', offset=0.0)
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_profile_by_area(component=core_structural_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth) - calculate_circle_area(AppConfig.HoleRadius), depth=AppConfig.LayerDepth, name='bg-rect')

        # Structural Component - Border
        if not component_exist(root_comp, 'border'):
            border_comp = create_component(root_component=root_comp, name="border")
            draw_border(component=border_comp, originalWidth=AppConfig.MaxLength, originalHeight=AppConfig.MaxWidth, borderDepth=AppConfig.LayerDepth, borderWidth=1.28, name='border', offset=0.0)
        
        # Structural Component - Main Design
        if not component_exist(root_comp, 'core'):
            main_comp = create_component(root_component=root_comp, name="core")
            extrudes = main_comp.features.extrudeFeatures
            
            sketch = create_sketch(main_comp, 'angled-rectangles-outer', offset=AppConfig.LayerDepth)
            draw_rotated_rectangle(sketch=sketch, width=64.0, height=64.0)
            extrude_thin(component=main_comp, sketch=sketch, strokeWeight=0.64, depth=1.28)
            
            sketch = create_sketch(main_comp, 'angled-rectangles-middle', offset=AppConfig.LayerDepth)
            draw_rotated_rectangle(sketch=sketch, width=64.0 - 16.0, height=64.0 - 16.0) 
            extrude_thin(component=main_comp, sketch=sketch, strokeWeight=0.64, depth=1.28)

            sketch = create_sketch(main_comp, 'angled-rectangles-inner', offset=AppConfig.LayerDepth)            
            draw_rotated_rectangle(sketch=sketch, width=32.0, height=32.0)
            extrude_thin(component=main_comp, sketch=sketch, strokeWeight=0.64, depth=1.28)
            
            sketch = create_sketch(main_comp, 'astroid-64', offset=AppConfig.LayerDepth)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=64.0, scaleY=64.0, strokeWeight=1.28)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(64.0) - calculate_astroid_area(64.0 - 1.28), depth=1.28, name='astroid-64')

            sketch = create_sketch(main_comp, 'astroid-32', offset=AppConfig.LayerDepth)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=32.0 + 8.0, scaleY=32.0 + 8.0, strokeWeight=1.28)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(32.0 + 8.0) - calculate_astroid_area(32.0 + 8.0 - 1.28), depth=1.28, name='astroid-32')
            
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw_border(component, originalWidth, originalHeight, borderDepth, borderWidth, name, offset=0.0):
    sketch = create_sketch(component, name, offset)
    
    # Define the corner points for the border rectangles
    # Calculations account for original rectangle size plus the border on each side
    extendedWidth = originalWidth + 2 * borderWidth
    extendedHeight = originalHeight + 2 * borderWidth
    
    # Top Border Rectangle
    topBorderTopLeft = adsk.core.Point3D.create(-extendedWidth / 2, originalHeight / 2 + borderWidth, 0)
    topBorderBottomRight = adsk.core.Point3D.create(extendedWidth / 2, originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(topBorderTopLeft, topBorderBottomRight)
    
    # Bottom Border Rectangle
    bottomBorderTopLeft = adsk.core.Point3D.create(-extendedWidth / 2, -originalHeight / 2 - borderWidth, 0)
    bottomBorderBottomRight = adsk.core.Point3D.create(extendedWidth / 2, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(bottomBorderTopLeft, bottomBorderBottomRight)
    
    # Left Border Rectangle
    leftBorderTopLeft = adsk.core.Point3D.create(-originalWidth / 2 - borderWidth, originalHeight / 2, 0)
    leftBorderBottomRight = adsk.core.Point3D.create(-originalWidth / 2, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(leftBorderTopLeft, leftBorderBottomRight)
    
    # Right Border Rectangle
    rightBorderTopLeft = adsk.core.Point3D.create(originalWidth / 2, originalHeight / 2, 0)
    rightBorderBottomRight = adsk.core.Point3D.create(originalWidth / 2 + borderWidth, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(rightBorderTopLeft, rightBorderBottomRight)
    
    # Extrusion of border rectangles could follow here, similar to how the bg-rect was extruded
    # Assuming you'd extrude these borders with the same or different depth as needed
    # Extrude if needed
    # Extrude if needed
    if AppConfig.Extrude:
        # Extrude each border rectangle individually
        extrudes = component.features.extrudeFeatures
        largestArea = 0
        # First, find the largest profile area to identify the inner profile to skip
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            if area > largestArea:
                largestArea = area
        
        # Now, extrude only the profiles that are not the largest (assuming borders have smaller area)
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            if area < largestArea:
                # This profile is not the inner profile, so extrude it
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                distance = adsk.core.ValueInput.createByReal(borderDepth)  # Depth of the extrusion for each border
                extrudeInput.setDistanceExtent(False, distance)
                extrudes.add(extrudeInput)

def create_seed_of_life(component: adsk.fusion.Component, radius=8.0, layer_depth=0.1, layer_offset=0.0, radius_diff=0.1, strokeWeight=0.05, extrudeHeight=0.1, n=3, fp_tolerance=0.1):
    try:
        sketches = component.sketches
        extrudes = component.features.extrudeFeatures
                
        # angle multiplier
        angle_mult = 30

        # Main code to create the Seed of Life and extrude
        for i in range(n):  # Creating 3 layers
            sketch = create_sketch(component, 'seed-of-life-' + str(i + 1), layer_offset + layer_depth * i)
            draw_seed_of_life_pattern(sketch, radius - i * (radius_diff * 2), 0, 0, angle_mult * i)
            
            # Thin Extrude the Seed of Life 
            for profile in sketch.profiles:
                # Thin Extrude
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                
                # Set the extrude to be a thin extrusion with a specified thickness.
                extrudeInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Side1, adsk.core.ValueInput.createByReal(strokeWeight))
                
                # Extrude Height
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
                
                # Create the extrusion.
                extrudes.add(extrudeInput)

    except:
        raise Exception('Failed:\n{}'.format(traceback.format_exc()))

def create_inverted_triangle(component, side_length, center_x=0, center_y=0, n=3, layer_depth=0.1, extrudeHeight=0.1, layer_offset=0.0):
    """
    Creates inverted triangles with two options: fill-based or stroke-based.
    For stroke-based, it draws smaller triangles inside the larger triangles and extrudes the space between them.
    
    Parameters:
    - component: The root component in which the sketches are to be created.
    - side_length: The length of the side of the triangles.
    - center_x, center_y: The center position of the composite shape.
    - n: The number of layers to create.
    - layer_depth: The depth between each layer.
    - type: The type of triangles to create ('fill' or 'stroke').
    """
    sketches = component.sketches
    extrudes = component.features.extrudeFeatures
    
    def create_triangles(sketch, side_length, center_x, center_y, type):
        # Base triangle height
        height = (math.sqrt(3) / 2) * side_length
        # Define vertices for both triangles
        vertices_up = [
            (center_x, center_y + 2 * height / 3),  # Top vertex of upward triangle
            (center_x - side_length / 2, center_y - height / 3),  # Bottom left vertex
            (center_x + side_length / 2, center_y - height / 3)   # Bottom right vertex
        ]
        
        vertices_down = [
            (center_x, center_y - 2 * height / 3),  # Bottom vertex of downward triangle
            (center_x - side_length / 2, center_y + height / 3),  # Top left vertex
            (center_x + side_length / 2, center_y + height / 3)   # Top right vertex
        ]

        def add_line(start_point, end_point):
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(*start_point), 
                adsk.core.Point3D.create(*end_point)
            )

        def draw_triangle(vertices, shrink_factor=0):
            if shrink_factor:
                center = (center_x, center_y)
                shrinked_vertices = [
                    (v[0] + (center[0] - v[0]) * shrink_factor, v[1] + (center[1] - v[1]) * shrink_factor)
                    for v in vertices
                ]
                for i in range(len(shrinked_vertices)):
                    start_point = shrinked_vertices[i]
                    end_point = shrinked_vertices[(i + 1) % len(shrinked_vertices)]
                    add_line(start_point, end_point)
            else:
                for i in range(len(vertices)):
                    start_point = vertices[i]
                    end_point = vertices[(i + 1) % len(vertices)]
                    add_line(start_point, end_point)

        # Draw outer triangles
        draw_triangle(vertices_up)
        draw_triangle(vertices_down)

        if type == 'stroke':
            # Draw inner triangles for the stroke effect
            draw_triangle(vertices_up, shrink_factor=0.1)
            draw_triangle(vertices_down, shrink_factor=0.1)
        
        # Extrude the space between the outer and inner triangles if 'stroke', else extrude the whole profile for 'fill'
        if type == 'stroke':
            for profile in sketch.profiles:
                if profile.areaProperties().area > 170:  # Adjust this threshold based on your design needs
                    continue
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))  # Set extrusion depth
                extrudes.add(extrudeInput)
        elif type == 'fill':
            for profile in sketch.profiles:
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
                extrudes.add(extrudeInput)
    
    
    # Create Base
    offsetPlane = create_offset_plane(component, layer_offset)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'base'
    create_triangles(sketch, side_length, center_x, center_y, 'fill')
    
    # Create layers
    offsetPlane = create_offset_plane(component, layer_offset + layer_depth)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'layer-1'
    create_triangles(sketch, side_length, center_x, center_y, 'stroke')
    
def extrude_thin(component: adsk.fusion.Component, sketch: adsk.fusion.Sketch, strokeWeight, depth):
    extrudes = component.features.extrudeFeatures
    for profile in sketch.profiles:
        # Thin Extrude
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        # Set the extrude to be a thin extrusion with a specified thickness.
        extrudeInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Side1, adsk.core.ValueInput.createByReal(strokeWeight))
        
        # Extrude Height
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
        
        # Create the extrusion.
        extrudes.add(extrudeInput)