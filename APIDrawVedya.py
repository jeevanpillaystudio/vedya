import random
import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .shapes import create_power_series_multiples, draw_astroid_stroke, calculate_astroid_area, draw_circle, calculate_circle_area, calculate_rectangle_area, draw_rectangle, draw_rotated_rectangle, create_seed
from .utils import create_array_random_unique_multiples, create_offset_plane, create_sketch, extrude_profile_by_area, component_exist, create_component, extrude_thin_one, log

# structurally
# 1 layer; each having 4 sub-layers
# 1 sub-layer == 0.32cm
# 1 layer == 1.28cm
# total layers = 4
# total depth = 5.12cm
# base = 6.4cm - 5.12cm = 1.28cm

class ScaleConfig():
    def __init__(self):
        pass
    
    Print3D = True
    ScaleFactor: float = 8.0 if Print3D else 1.0
    
    def __str__(self) -> str:
        return f"ScaleConfig: ScaleFactor={self.ScaleFactor}"
        
class AppConfig():
    """
    List of the configurations for the creation
    """
    def __init__(self):
        pass
    def __str__(self) -> str:
        return f"AppConfig: HoleRadius={self.HoleRadius}, Extrude={self.Extrude}, MaxWidth={self.MaxWidth}, MaxLength={self.MaxLength}, LayerDepth={self.LayerDepth}, Seed={self.Seed}"
    Extrude = True
    
    HoleRadius = 8.0 / ScaleConfig.ScaleFactor
    MaxWidth = 128.0 / ScaleConfig.ScaleFactor
    MaxLength = 128.0 / ScaleConfig.ScaleFactor
    LayerDepth = 1.28 / ScaleConfig.ScaleFactor
    
    Seed = create_seed()
    
class DiagonalRectangleConfig():
    def __init__(self):
        pass
    def __str__(self) -> str:
        return f"DiagonalRectangleConfig: NumPoints={self.NumPoints}, StrokeWeight={self.StrokeWeight}, OuterDiagonalRectangleWidth={self.OuterDiagonalRectangleWidth}, OuterDiagonalRectangleHeight={self.OuterDiagonalRectangleHeight}, MiddleDiagonalRectangleWidth={self.MiddleDiagonalRectangleWidth}, MiddleDiagonalRectangleHeight={self.MiddleDiagonalRectangleHeight}, InnerDiagonalRectangleWidth={self.InnerDiagonalRectangleWidth}, InnerDiagonalRectangleHeight={self.InnerDiagonalRectangleHeight}"
    OuterDiagonalRectangleWidth = 64.0 / ScaleConfig.ScaleFactor
    OuterDiagonalRectangleHeight = 64.0 / ScaleConfig.ScaleFactor
    OuterDiagonalRectangleStrokeWeight = 0.64 / ScaleConfig.ScaleFactor
    
    MiddleDiagonalRectangleWidth = (64.0 - 16.0) / ScaleConfig.ScaleFactor
    MiddleDiagonalRectangleHeight = (64.0 - 16.0) / ScaleConfig.ScaleFactor
    MiddleDiagonalRectangleStrokeWeight = 0.64 / ScaleConfig.ScaleFactor
    
    InnerDiagonalRectangleWidth = 32.0 / ScaleConfig.ScaleFactor
    InnerDiagonalRectangleHeight = 32.0 / ScaleConfig.ScaleFactor
    InnerDiagonalRectangleStrokeWeight = 0.64 / ScaleConfig.ScaleFactor 
    
class AstroidConfig():
    def __init__(self):
        pass
    def __str__(self) -> str:
        return f"AstroidConfig: NumPoints={self.NumPoints}, N={self.N}, OuterAstroidRadius={self.OuterAstroidRadius}, InnerAstroidRadius={self.InnerAstroidRadius}"
    N = 2/3
    NumPoints = 128
    
    OuterAstroidRadius = 64.0 / ScaleConfig.ScaleFactor
    OuterAstroidStrokeWeight = 1.28 / ScaleConfig.ScaleFactor
    
    InnerAstroidRadius = (32.0 + 8.0) / ScaleConfig.ScaleFactor
    InnerAstroidStrokeWeight = 1.28 / ScaleConfig.ScaleFactor
    
class KailashConfig():
    def __init__(self):
        pass
    KailashIntersectExtrudeArea = 2130.679120238867 / ScaleConfig.ScaleFactor ** 2 # this is the area of the intersected extrusion of the kailash terrain, manually created. @todo - automate this

class SeedOfLifeConfig():
    def __init__(self):
        pass
    MinRandomMultiple = 2
    MaxRandomMultiple = 4
    MinNumLayers = 1
    MaxNumLayers = 2
    RepeatValues = create_power_series_multiples(3) # the values of the iterator repeat can only be either 1, 2 or 4 times; e.g [1, 2, 4]
    
    AngleDifference = 30
    
    StrokeWeight = 0.32 / ScaleConfig.ScaleFactor
    RadiusReduceDistance = 0.32 / ScaleConfig.ScaleFactor
    
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
        
        # Log the seed for reproducibility
        app_config = AppConfig()
        log(app_config)

        # Get the root component of the active design
        root_comp: adsk.fusion.Component = design.rootComponent
        
        # Structural Component - Background
        if not component_exist(root_comp, create_component_name('bg')):
            core_structural_comp = create_component(root_component=root_comp, component_name=create_component_name("bg"))
            sketch = create_sketch(core_structural_comp, 'bg-rect', offset=0.0)
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_profile_by_area(component=core_structural_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth) - calculate_circle_area(AppConfig.HoleRadius), depth=AppConfig.LayerDepth, name='bg-rect')
        
        # Structural Component - Border
        if not component_exist(root_comp, create_component_name('border')):
            border_comp = create_component(root_component=root_comp, component_name=create_component_name("border"))
            draw_border(component=border_comp, originalWidth=AppConfig.MaxLength, originalHeight=AppConfig.MaxWidth, borderDepth=AppConfig.LayerDepth * 2, borderWidth=AppConfig.LayerDepth, name='border', offset=0.0)
        
        # Structural Component - Core Design
        if not component_exist(root_comp, create_component_name('core')):
            main_comp = create_component(root_component=root_comp, component_name=create_component_name("core"))
            
            sketch = create_sketch(main_comp, 'angled-rectangles-outer', offset=AppConfig.LayerDepth)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight)
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=AppConfig.LayerDepth, strokeWeight=DiagonalRectangleConfig.OuterDiagonalRectangleStrokeWeight, name="extrude-thin", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            sketch = create_sketch(main_comp, 'angled-rectangles-middle', offset=AppConfig.LayerDepth)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight) 
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=AppConfig.LayerDepth, strokeWeight=DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight, name="extrude-thin", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            sketch = create_sketch(main_comp, 'angled-rectangles-inner', offset=AppConfig.LayerDepth)            
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=AppConfig.LayerDepth, strokeWeight=DiagonalRectangleConfig.InnerDiagonalRectangleStrokeWeight, name="extrude-thin", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            sketch = create_sketch(main_comp, 'astroid-64', offset=AppConfig.LayerDepth)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.OuterAstroidRadius) - calculate_astroid_area(AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight), depth=AppConfig.LayerDepth, name='astroid-64')

            sketch = create_sketch(main_comp, 'astroid-32', offset=AppConfig.LayerDepth)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius, strokeWeight=AstroidConfig.InnerAstroidStrokeWeight)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius) - calculate_astroid_area(AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight), depth=AppConfig.LayerDepth, name='astroid-32')
            
            # @todo convert this use Side1 and Side2, and remove 0.64 / 8 hack 
            sketch = create_sketch(main_comp, 'hole-thin-circle', offset=AppConfig.LayerDepth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius + 0.64 / 8)
            extrude_thin_one(component=main_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.LayerDepth, strokeWeight=0.64 / 8, name='hole-thin-circle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            
        # Structural Component - Kailash Terrain Generation Sketch
        # Note: This is a placeholder for the actual terrain generation code. Requires manual intervention using STL files & Fusion Forms.
        # Guide: https://www.youtube.com/watch?v=Ea_YC4Jh0Sw
        if not component_exist(root_comp, create_component_name('kailash')):
            kailash_comp = create_component(root_component=root_comp, component_name=create_component_name("kailash"))
            sketch = create_sketch(kailash_comp, 'kailash-terrain', offset=AppConfig.LayerDepth)
            
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth) 
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight) 
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius, strokeWeight=AstroidConfig.InnerAstroidStrokeWeight) 
            
        # Structural Component - Seed of Life
        if not component_exist(root_comp, create_component_name('seed-of-life')):
            seed_of_life_comp = create_component(root_component=root_comp, component_name=create_component_name("seed-of-life"))
            
            # draw from middle
            center_x = 0
            center_y = 0
            
            # iterate; the enumerator is an array of multiples of 8; e.g [8, 16, 24, 32, 40, 48, 56, 64]
            for (_, radius) in enumerate(create_array_random_unique_multiples(size=random.randint(SeedOfLifeConfig.MinRandomMultiple, SeedOfLifeConfig.MaxRandomMultiple), multiple=1, min_multiple=1, max_multiple=10)):
                # select number of layers to create for each generation
                n = random.randint(SeedOfLifeConfig.MinNumLayers, SeedOfLifeConfig.MaxNumLayers)
                
                # repeats
                # repeat = random.choice(SeedOfLifeConfig.RepeatValues)
                repeat = 2
                
                # extrusion height; each layer has the same distance between them
                extrude_height_per_layer = AppConfig.LayerDepth / repeat
                
                # repeat j many times; this gives the "depth" effect
                for j in range(repeat):
                    # each seed of life generated here
                    for i in range(n):
                        # the statart of the seed-of-life layer + the offset of the each sub-layer
                        plane_offset = AppConfig.LayerDepth 
                        
                        # radius, strokeWeight, extrudeHeight difference each layer is based on j; gives it the "depth" effect
                        r = radius - (SeedOfLifeConfig.RadiusReduceDistance * j) / 2
                        eh = extrude_height_per_layer * (j + 1)
                        sw = SeedOfLifeConfig.StrokeWeight
                        log(f"seed-of-life: {n} circles with radius: {r} and strokeWeight: {sw} and extrudeHeight: {eh}")
                        
                        # center circle
                        sketch = create_sketch(seed_of_life_comp, 'seed-of-life-' + str(r) + '-center', plane_offset)
                        draw_circle(sketch, r, center_x, center_y)
                        extrude_thin_one(component=seed_of_life_comp, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-center-' + str(r), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                        
                        # draw; this is a standard seed of life algorithm.
                        for i in range(6):
                            # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
                            angle = math.radians(i * 60)
                            x = center_x + r * math.cos(angle)
                            y = center_y + r * math.sin(angle)
                            sketch = create_sketch(seed_of_life_comp, 'seed-of-life-' + str(r) + "-" + str(angle), plane_offset)
                            draw_circle(sketch, r, x, y)
                            extrude_thin_one(component=seed_of_life_comp, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-' + str(r) + "-" + str(sw), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                
                # log the seed of life
                log(f"seed-of-life: {n} circles with radius: {radius}")

            # cut a hole in the center
            try:
                sketch = create_sketch(seed_of_life_comp, 'cut-hole', offset=AppConfig.LayerDepth)
                draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
                extrude_profile_by_area(component=seed_of_life_comp, profiles=sketch.profiles, area=calculate_circle_area(AppConfig.HoleRadius), depth=AppConfig.LayerDepth, name='cut-hole', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
            except:
                log("cut-hole: none to cut")
           
            # cut kailash intersection 
            try:
                sketch = create_sketch(seed_of_life_comp, 'cut-kailash-intersection', offset=AppConfig.LayerDepth)
                draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight)
                draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
                draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
                draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius, strokeWeight=AstroidConfig.InnerAstroidStrokeWeight) 
                
                # for profile in sketch.profiles:
                #     log(f"cut-kailash-intersection: {profile.areaProperties().area}")
                
                extrude_profile_by_area(component=seed_of_life_comp, profiles=sketch.profiles, area=KailashConfig.KailashIntersectExtrudeArea, depth=AppConfig.LayerDepth, name='cut-kailash-intersection', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
            except:
                log("cut-kailash-intersection: none to cut")

            # cut all the circles that is out of bounds
            try:
                sketch = create_sketch(seed_of_life_comp, 'intersect-only-in-bounds', offset=AppConfig.LayerDepth)
                draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
                extrude_profile_by_area(component=seed_of_life_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), depth=AppConfig.LayerDepth, name='intersect-only-in-bounds', operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation)
            except:
                log("intersect-only-in-bounds: none to cut")
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

def create_inverted_triangle(component, side_length, center_x=0, center_y=0, n=3, layer_depth=0.1, extrudeHeight=0.1, layer_offset=0.0):
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
    
def create_component_name(name):
    if ScaleConfig.Print3D:
        return f"3d-{name}"
    return f"{name}"
