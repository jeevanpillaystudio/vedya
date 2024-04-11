from enum import Enum
import random
import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .shapes import calculate_three_point_rectangle_area, create_power_series_multiples, draw_astroid_stroke, calculate_astroid_area, draw_circle, calculate_circle_area, calculate_rectangle_area, draw_rectangle, draw_rotated_rectangle, create_seed
from .utils import copy_body, create_array_random_unique_multiples, create_offset_plane, create_sketch, extrude_profile_by_area, component_exist, create_component, extrude_thin_one, log, move_body, scale_body, timer

class ScaleConfig():
    def __init__(self):
        pass
    
    Print3D = True
    ScaleFactor: float = 8.0 if Print3D else 1.0
    
    def __str__(self) -> str:
        return f"ScaleConfig: ScaleFactor={self.ScaleFactor}"
    
class DesignMode:
    def __init__(self):
        pass
    DirectDesign = adsk.fusion.DesignTypes.DirectDesignType
    ParametricDesign = adsk.fusion.DesignTypes.ParametricDesignType
        
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
    
    BorderWidth = 1.28 / ScaleConfig.ScaleFactor
    BorderDepth = (1.28 * 2) / ScaleConfig.ScaleFactor
    
    Seed = create_seed()
    DesignMode = DesignMode.DirectDesign
 
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
    AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea = 1.2765358608164958
    OuterDiagonalCutWithAstroidExtrudeArea = 12.375340707128288

class SeedOfLifeConfig():
    def __init__(self):
        pass
    MinRandomMultiple = 2
    MaxRandomMultiple = 4
    DepthRepeatValues = create_power_series_multiples(1) # the values of the iterator repeat can only be either 1, 2 or 4 times; e.g [1, 2, 4]
    
    AngleDifference = 30
    
    StrokeWeight = 0.32 / ScaleConfig.ScaleFactor
    RadiusReduceDistance = 0.32 / ScaleConfig.ScaleFactor

@timer 
def run(context):
    ui = None
    try:
        # Get the application and root component
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
            
        # check if the design is not in "Design" mode.
        if not design:
            ui.messageBox('It is not supported in current workspace, please switch to DESIGN workspace and try again.')
            return
    
        # select design mode
        design.designType = AppConfig.DesignMode
        log(f'Design Mode: {AppConfig.DesignMode}')
        
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
            sketch = create_sketch(border_comp, 'border', offset=0.0)
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength + AppConfig.BorderWidth * 2, width=AppConfig.MaxWidth + AppConfig.BorderWidth * 2)
            extrude_thin_one(component=border_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.BorderDepth, strokeWeight=AppConfig.BorderWidth, name='border', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
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
            
        # Structural Component - Seed of Life
        if not component_exist(root_comp, create_component_name('seed-of-life')):
            seed_of_life_comp = create_component(root_component=root_comp, component_name=create_component_name("seed-of-life"))
            
            # draw from middle
            center_x = 0
            center_y = 0
            
            # iterate; the enumerator is an array of multiples of 8; e.g [8, 16, 24, 32, 40, 48, 56, 64]
            for (_, initial_radius) in enumerate(create_array_random_unique_multiples(size=random.randint(SeedOfLifeConfig.MinRandomMultiple, SeedOfLifeConfig.MaxRandomMultiple), multiple=8 / ScaleConfig.ScaleFactor, min_multiple=1, max_multiple=10)):
                # repeats
                depth_repeat = random.choice(SeedOfLifeConfig.DepthRepeatValues)
                
                # extrusion height; each layer has the same distance between them
                extrude_height_per_layer = AppConfig.LayerDepth / depth_repeat
                
                # log
                log(f"INIT seed-of-life: depth-repeat {depth_repeat}, initial-radius: {initial_radius}, extrude-height-per-layer: {extrude_height_per_layer}")
                
                # repeat j many times; this gives the "depth" effect
                for j in range(depth_repeat):
                    create_seed_of_life(seed_of_life_comp, center_x, center_y, initial_radius, j, extrude_height_per_layer)
                    
                    
            # # cut with OuterDiagonalCutWithAstroidExtrudeArea
            # sketch = create_sketch(seed_of_life_comp, 'seed-of-life-outer-cut', offset=AppConfig.LayerDepth)
            # draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
            # draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight)
            # draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
            # extrude_profile_by_area(component=seed_of_life_comp, profiles=sketch.profiles, area=KailashConfig.OuterDiagonalCutWithAstroidExtrudeArea, depth=AppConfig.LayerDepth, name='seed-of-life-outer-cut', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
                    
        # Structural Component - Interstellar Tesellation
        # if not component_exist(root_comp, create_component_name('interstellar-tesellation')):
        #     interstellar_tesellation_comp = create_component(root_component=root_comp, component_name=create_component_name("interstellar-tesellation"))
            
        #     # draw from middle
        #     center_x = 0
        #     center_y = 0
        #     depth_repeat = 6
        #     extrude_height_per_layer = AppConfig.LayerDepth / 2
            
        #     for j in range(depth_repeat):
        #         layer_offset = ((j + 1) * 4)
                
        #         # create center brace around outer diagonal rectangle
        #         sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-center-brace', offset=AppConfig.LayerDepth)
        #         draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth - (DiagonalRectangleConfig.OuterDiagonalRectangleStrokeWeight * layer_offset), height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight - (DiagonalRectangleConfig.OuterDiagonalRectangleStrokeWeight * layer_offset))
        #         extrude_thin_one(component=interstellar_tesellation_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=DiagonalRectangleConfig.OuterDiagonalRectangleStrokeWeight, name='interstellar-tesellation-center-brace', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                
        #     # cut with AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea
        #     sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-astroid-outer-cut', offset=AppConfig.LayerDepth)
        #     draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
        #     draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
        #     extrude_profile_by_area(component=interstellar_tesellation_comp, profiles=sketch.profiles, area=KailashConfig.AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea, depth=AppConfig.LayerDepth, name='interstellar-tesellation-astroid-outer-cut', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
                    
        # Structural Component - Corner Seed of Life
        # if not component_exist(root_comp, create_component_name('corner-seed-of-life')):
        #     corner_seed_of_life_comp = create_component(root_component=root_comp, component_name=create_component_name("corner-seed-of-life"))
            
        #     # iterate; the enumerator is an array of multiples of 8; e.g [8, 16, 24, 32, 40, 48, 56, 64]
        #     for (_, initial_radius) in enumerate(create_array_random_unique_multiples(size=random.randint(SeedOfLifeConfig.MinRandomMultiple, SeedOfLifeConfig.MaxRandomMultiple), multiple=8 / ScaleConfig.ScaleFactor, min_multiple=1, max_multiple=4)):
                
        #         for i in range(4):
        #             # start at each corner of the bg
        #             center_x = AppConfig.MaxLength / 2 if i % 2 == 0 else -AppConfig.MaxLength / 2
        #             center_y = AppConfig.MaxWidth / 2 if i < 2 else -AppConfig.MaxWidth / 2
                    
        #             # repeats
        #             depth_repeat = random.choice(SeedOfLifeConfig.DepthRepeatValues)
                    
        #             # extrusion height; each layer has the same distance between them
        #             extrude_height_per_layer = AppConfig.LayerDepth / depth_repeat
                    
        #             # log
        #             log(f"INIT corner-seed-of-life: depth-repeat {depth_repeat}, initial-radius: {initial_radius}, extrude-height-per-layer: {extrude_height_per_layer}")
                    
        #             # repeat j many times; this gives the "depth" effect
        #             for j in range(depth_repeat):
        #                 create_seed_of_life(corner_seed_of_life_comp, center_x, center_y, initial_radius, j, extrude_height_per_layer)
            
        if not component_exist(root_comp, create_component_name('torus')):
            torus_comp = create_component(root_component=root_comp, component_name=create_component_name("torus"))
            
            # inner torus
            # iterations = 16
            # initial_radius = 16.0 / ScaleConfig.ScaleFactor
            # # stroke_weight = 0.64 / ScaleConfig.ScaleFactor / 2
            # stroke_weight = 0.64 / ScaleConfig.ScaleFactor
            # # extrude_height = AppConfig.LayerDepth / 4
            # extrude_height = AppConfig.LayerDepth
            # inner_torus_component = create_component(root_component=torus_comp, component_name=create_component_name("torus-inner-" + str(initial_radius) + "-" + str(iterations)))
            # create_torus(root_component=inner_torus_component, center_x=0, center_y=0, radius=initial_radius, iterations=iterations, stroke_weight=stroke_weight, extrude_height=extrude_height, layer_offset=AppConfig.LayerDepth)
            
            # outer torus
            iterations = 16
            radius = 32.0 / ScaleConfig.ScaleFactor
            stroke_weight = 0.64 / ScaleConfig.ScaleFactor
            outer_torus_component = create_component(root_component=torus_comp, component_name=create_component_name("torus-outer-" + str(radius) + "-" + str(iterations)))
            depth_repeat = 4
            start_layer_offset = AppConfig.LayerDepth 
            extrude_height = AppConfig.LayerDepth / depth_repeat

            for i in range(depth_repeat):
                # layer offset (runs reverse)
                layer_offset = start_layer_offset + extrude_height * i
                
                # stroke weight starts depth_repeat times and reduces each round
                sw = stroke_weight * (depth_repeat - i)
                
                # radius same
                r = radius
                
                # create inner comp
                torus_inner_component = create_component(root_component=outer_torus_component, component_name=create_component_name("torus-inner-" + str(r) + "-" + str(sw)))
                
                # create
                create_torus(root_component=torus_inner_component, center_x=0, center_y=0, radius=radius, iterations=iterations, stroke_weight=sw, extrude_height=extrude_height, layer_offset=layer_offset) 
         
        try:
            cut_hole_comp = create_component(root_component=root_comp, component_name=create_component_name("cut-hole"))
            sketch = create_sketch(cut_hole_comp, 'cut-hole', offset=AppConfig.LayerDepth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_profile_by_area(component=cut_hole_comp, profiles=sketch.profiles, area=calculate_circle_area(AppConfig.HoleRadius), depth=AppConfig.LayerDepth * 2, name='cut-hole', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
        except:
            log("cut-hole: none to cut")
            
        # Structural Component - Kailash Terrain Generation Sketch
        # Note: This is a placeholder for the actual terrain generation code. Requires manual intervention using STL files & Fusion Forms.
        # Guide: https://www.youtube.com/watch?v=Ea_YC4Jh0Sw
        try:
            kailash_comp = create_component(root_component=root_comp, component_name=create_component_name("cut-kailash-intersection"))
            sketch = create_sketch(kailash_comp, 'cut-kailash-intersection', offset=AppConfig.LayerDepth)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
            draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius, strokeWeight=AstroidConfig.InnerAstroidStrokeWeight) 
            extrude_profile_by_area(component=kailash_comp, profiles=sketch.profiles, area=KailashConfig.KailashIntersectExtrudeArea, depth=AppConfig.LayerDepth, name='cut-kailash-intersection', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
        except:
            log("cut-kailash-intersection: none to cut")
                
                
        # intersect only in bounds
        try:
            intersect_only_in_bounds_comp = create_component(root_component=root_comp, component_name=create_component_name("intersect-only-in-bounds"))
            sketch = create_sketch(intersect_only_in_bounds_comp, 'intersect-only-in-bounds', offset=AppConfig.LayerDepth)
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
            extrude_profile_by_area(component=intersect_only_in_bounds_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), depth=AppConfig.LayerDepth, name='intersect-only-in-bounds', operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation)
        except:
            log("intersect-only-in-bounds: none to cut")
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

@timer
def create_seed_of_life(root_component: adsk.fusion.Component, center_x, center_y, radius, j, extrude_height_per_layer):
    # the statart of the seed-of-life layer + the offset of the each sub-layer
    plane_offset = AppConfig.LayerDepth 
                
    # radius, strokeWeight, extrudeHeight difference each layer is based on j; gives it the "depth" effect
    r = radius - (SeedOfLifeConfig.RadiusReduceDistance * j) / 2
    eh = extrude_height_per_layer * (j + 1)
    sw = SeedOfLifeConfig.StrokeWeight
    log(f"CREATE seed-of-life-inner: radius: {r} and strokeWeight: {sw} and extrudeHeight: {eh}")
                
    # draw the center circle
    sketch = create_sketch(root_component, 'seed-of-life-' + str(r) + '-center', plane_offset)
    draw_circle(sketch, r, center_x, center_y)
    initial_body = extrude_thin_one(component=root_component, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-center-' + str(r), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    initial_body.name = 'seed-of-life-center-' + str(r)
    
    # draw; this is a standard seed of life algorithm.
    for i in range(6):
        # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
        angle = math.radians(i * 60)
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)

        # draw
        if AppConfig.DesignMode == DesignMode.DirectDesign:
            sketch = create_sketch(root_component, 'seed-of-life-' + str(r) + "-" + str(angle), plane_offset)
            draw_circle(sketch, r, x, y)
            extrude_thin_one(component=root_component, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-' + str(r) + "-" + str(angle), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)        
        elif AppConfig.DesignMode == DesignMode.ParametricDesign:
            real_body = copy_body(root_component, initial_body, name='seed-of-life-' + str(r) + "-" + str(angle))
            move_body(root_component, x, y, real_body)
        else:
            raise Exception("DesignMode not supported")

@timer
def create_torus(root_component: adsk.fusion.Component, center_x, center_y, radius, iterations, stroke_weight, extrude_height, layer_offset):
    sketch = create_sketch(root_component, 'torus-outer-circle-' + str(radius) + "-" + str(iterations), offset=layer_offset)
    
    # draw the outer circle
    draw_circle(sketch, radius, center_x, center_y)
    initial_body = extrude_thin_one(component=root_component, profile=sketch.profiles[0], extrudeHeight=extrude_height, strokeWeight=stroke_weight, name='torus-outer-circle' + str(radius) + "-" + str(iterations), operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    initial_body.name = 'torus-outer-circle' + str(radius) + "-" + str(iterations)
    
    # draw throwaway circle (remove at the end) with scale non-uniform; x, y = 0.5
    if AppConfig.DesignMode == DesignMode.DirectDesign:
        pass        
    elif AppConfig.DesignMode == DesignMode.ParametricDesign:
        throwaway_body = copy_body(root_component, initial_body, name='torus-outer-circle-throwaway-' + str(radius) + "-" + str(iterations))
        scale_body(root_component=root_component, body=throwaway_body, scale_x=0.5, scale_y=0.5, scale_z=1, sketch_pt=sketch.sketchPoints.item(0))
    else:
        raise Exception("DesignMode not supported")
                
    # create the torus
    angle_per_iteration = 360 / iterations
    r = radius / 2.0
    
    # draw; this is a standard torus algorithm.
    for i in range(iterations):
        # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
        angle = math.radians(i * angle_per_iteration)
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)
        
        # draw
        if AppConfig.DesignMode == DesignMode.DirectDesign:
            real_sketch = create_sketch(root_component, 'torus-inner-circle-' + str(r) + "-" + str(angle), layer_offset)
            draw_circle(real_sketch, r, x, y)
            extrude_thin_one(component=root_component, profile=real_sketch.profiles[0], extrudeHeight=extrude_height, strokeWeight=stroke_weight, name='torus-inner-circle-' + str(r) + "-" + str(angle), operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation) 
        elif AppConfig.DesignMode == DesignMode.ParametricDesign:
            real_body = copy_body(root_component=root_component, body=throwaway_body, name='torus-inner-circle-' + str(r) + "-" + str(angle))
            move_body(root_component, x, y, real_body)
        else:
            raise Exception("DesignMode not supported")
                    
    # log the seed of life
    log(f"torus: {iterations} circles with radius: {r}")

def create_component_name(name):
    if ScaleConfig.Print3D:
        return f"3d-{name}"
    return f"{name}"
