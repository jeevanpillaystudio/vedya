import random
import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .shapes import calculate_three_point_rectangle_area, draw_astroid, draw_astroid_stroke, calculate_astroid_area, draw_circle, calculate_circle_area, calculate_rectangle_area, draw_rectangle, draw_rotated_rectangle, create_seed, draw_tesseract_projection
from .utils import DepthRepeat, combine_body, copy_body, create_array_random_unique_multiples, create_offset_plane, create_sketch, extrude_profile_by_area, component_exist, create_component, extrude_single_profile_by_area, extrude_thin_one, log, move_body, scale_body, timer, depth_repeat_iterator
import random

# test cuts
# 1. torus, torus invert
# 2. seed of life inverted layering
# 3. structural empty layer - the layer 8-11
# 4. layered terrain

# project layers
# 1. each layer is 0.48

class PrintType:
    def __init__(self) -> None:
        pass
    
    Print3D = 0.125 # 1/8
    Laser = 0.1875 # 3/16
    CNC = 1.0 # 1
    
    @classmethod
    def get_attr_name(cls, value):
        # Find the attribute by its value
        for attr in dir(cls):
            if getattr(cls, attr) == value and not attr.startswith('__'):
                return attr
        return None

class ScaleConfig():
    def __init__(self):
        pass
    
    ScaleFactor: float = PrintType.CNC
    
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
    
    HoleRadius = 4.0 * ScaleConfig.ScaleFactor
    MaxWidth = 96.0 * ScaleConfig.ScaleFactor
    MaxLength = 64.0 * ScaleConfig.ScaleFactor
    LayerDepth = 0.48 * ScaleConfig.ScaleFactor
    StrokeWeight = 0.96 * ScaleConfig.ScaleFactor
    
    BorderWidth = 1.28 * ScaleConfig.ScaleFactor
    BorderDepth = (1.28 * 2) * ScaleConfig.ScaleFactor
    
    Seed = create_seed()
    DesignMode = DesignMode.DirectDesign
    SlicerRecursiveDepthLimit = 4
    
    def aspect_ratio(self):
        return self.MaxLength / self.MaxWidth
    
    
class BackgroundConfig():
    def __init__(self):
        pass
    MaxWidth = AppConfig.MaxWidth
    MaxLength = AppConfig.MaxLength
    ExtrudeHeight = AppConfig.LayerDepth * 2 * ScaleConfig.ScaleFactor
 
class DiagonalRectangleConfig():
    def __init__(self):
        pass
    def __str__(self) -> str:
        return f"DiagonalRectangleConfig: NumPoints={self.NumPoints}, StrokeWeight={self.StrokeWeight}, OuterDiagonalRectangleWidth={self.OuterDiagonalRectangleWidth}, OuterDiagonalRectangleHeight={self.OuterDiagonalRectangleHeight}, MiddleDiagonalRectangleWidth={self.MiddleDiagonalRectangleWidth}, MiddleDiagonalRectangleHeight={self.MiddleDiagonalRectangleHeight}, InnerDiagonalRectangleWidth={self.InnerDiagonalRectangleWidth}, InnerDiagonalRectangleHeight={self.InnerDiagonalRectangleHeight}"
    OuterDiagonalRectangleWidth = 32.0 * ScaleConfig.ScaleFactor
    OuterDiagonalRectangleHeight = 32.0 * ScaleConfig.ScaleFactor
    OuterDiagonalRectangleStrokeWeight = 0.64 * ScaleConfig.ScaleFactor
    
    MiddleDiagonalRectangleWidth = (64.0 - 16.0) / (2.0) * ScaleConfig.ScaleFactor
    MiddleDiagonalRectangleHeight = (64.0 - 16.0) / (2.0) * ScaleConfig.ScaleFactor
    MiddleDiagonalRectangleStrokeWeight = 0.64 * ScaleConfig.ScaleFactor
    
    InnerDiagonalRectangleWidth = 32.0 / 2.0 * ScaleConfig.ScaleFactor
    InnerDiagonalRectangleHeight = 32.0 / 2.0 * ScaleConfig.ScaleFactor
    InnerDiagonalRectangleStrokeWeight = 0.64 * ScaleConfig.ScaleFactor 
    
class AstroidConfig():
    def __init__(self):
        pass
    def __str__(self) -> str:
        return f"AstroidConfig: NumPoints={self.NumPoints}, N={self.N}, OuterAstroidRadius={self.OuterAstroidRadius}, InnerAstroidRadius={self.InnerAstroidRadius}"
    N = 2/3
    NumPoints = 128
    
    OuterAstroidRadius = (32.0 - 2.56) * ScaleConfig.ScaleFactor
    OuterAstroidStrokeWeight = (AppConfig.StrokeWeight * ScaleConfig.ScaleFactor) * 2
    
    InnerAstroidRadius = (16.0 + 2.56) * ScaleConfig.ScaleFactor
    InnerAstroidStrokeWeight = (AppConfig.StrokeWeight * ScaleConfig.ScaleFactor) * 2
    
class KailashConfig():
    def __init__(self):
        pass
    # KailashIntersectExtrudeArea = 2130.679120238867 * ScaleConfig.ScaleFactor ** 2 # this is the area of the intersected extrusion of the kailash terrain, manually created. @todo - automate this
    KailashIntersectExtrudeArea = 24.69811845861016
    AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea = 1.2765358608164958
    OuterDiagonalCutWithAstroidExtrudeArea = 12.375340707128288

class SeedOfLifeConfig():
    def __init__(self):
        pass
    MinRandomMultiple = 1
    MaxRandomMultiple = 1
    # DepthRepeatValues = create_power_series_multiples(3) # the values of the iterator repeat can only be either 1, 2 or 4 times; e.g [1, 2, 4]
    DepthRepeatValues = [1]
    
    AngleDifference = 30
    
    StrokeWeight = 0.64 * ScaleConfig.ScaleFactor
    
class DepthEffect():
    def __init__(self):
        pass
    Side1 = adsk.fusion.ThinExtrudeWallLocation.Side1
    Side2 = adsk.fusion.ThinExtrudeWallLocation.Side2
    Center = adsk.fusion.ThinExtrudeWallLocation.Center

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
        
        # log the configurations
        app_config = AppConfig()
        log(app_config)
        
        # set seed
        random.seed(AppConfig.Seed)

        # Get the root component of the active design
        root_comp: adsk.fusion.Component = design.rootComponent
        
        # Slicer
        # first-layer = 1.28
        # second-layer = 1.28
        # third-layer = 1.28
        # fourth-layer = 1.28
        # slicer(root_component=root_comp, design=design, sliced_layer_depth=AppConfig.LayerDepth / 4, sliced_layer_count=12)
        # return
        
        # Structural Component - Background
        if not component_exist(root_comp, create_component_name('bg')):
            core_structural_comp = create_component(root_component=root_comp, component_name=create_component_name("bg"))
            sketch = create_sketch(core_structural_comp, 'bg-rect', offset=0.0)
            draw_rectangle(sketch=sketch, length=BackgroundConfig.MaxLength, width=BackgroundConfig.MaxWidth)
            extrude_profile_by_area(component=core_structural_comp, profiles=sketch.profiles, area=calculate_rectangle_area(BackgroundConfig.MaxLength, BackgroundConfig.MaxWidth), extrude_height=BackgroundConfig.ExtrudeHeight, name='bg-rect')

        # Structural Component - Border
        # if not component_exist(root_comp, create_component_name('border')):
        #     border_comp = create_component(root_component=root_comp, component_name=create_component_name("border"))
        #     sketch = create_sketch(border_comp, 'border', offset=0.0)
        #     draw_rectangle(sketch=sketch, length=AppConfig.MaxLength + AppConfig.BorderWidth * 2, width=AppConfig.MaxWidth + AppConfig.BorderWidth * 2)
        #     extrude_thin_one(component=border_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.BorderDepth * 2, strokeWeight=AppConfig.BorderWidth, name='border', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        # Structural Component - Core Design
        if not component_exist(root_comp, create_component_name('core')):
            main_comp = create_component(root_component=root_comp, component_name=create_component_name("core"))
            
            # level 2D -----------
            layer_offset = AppConfig.LayerDepth * 2
            
            # draw the rotated rectangle outer
            sketch = create_sketch(main_comp, 'angled-rectangles-outer-lower', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_three_point_rectangle_area(DiagonalRectangleConfig.OuterDiagonalRectangleWidth, DiagonalRectangleConfig.OuterDiagonalRectangleHeight), extrude_height=extrude_height, name='angled-rectangles-outer', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # level 2.5D ----------- 
            layer_offset = AppConfig.LayerDepth * 3
            
            # draw the rotated rectangle outer upper thin extrudes
            sketch = create_sketch(main_comp, 'angled-rectangles-outer-upper', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth * 2
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight)
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=extrude_height, strokeWeight=DiagonalRectangleConfig.OuterDiagonalRectangleStrokeWeight, name="angled-rectangles-outer", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # level 3D -----------
            layer_offset = AppConfig.LayerDepth * 3
            
            # draw the rotated rectangle middle
            sketch = create_sketch(main_comp, 'angled-rectangles-middle', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth * 2
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight) 
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=extrude_height, strokeWeight=DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight, name="angled-rectangles-middle", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                
            # draw the astroid 64
            sketch = create_sketch(main_comp, 'astroid-64-outer', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.OuterAstroidRadius), extrude_height=extrude_height, name='astroid-64-outer', fp_tolerance=1e0)
            
            # level 4D -----------
            layer_offset = AppConfig.LayerDepth * 4
            
            # draw the astroid 64 inner
            sketch = create_sketch(main_comp, 'astroid-64-inner', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight, scaleY=AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight), extrude_height=extrude_height, name='astroid-64-inner', fp_tolerance=1e0) 

            # level 5D -----------
            layer_offset = AppConfig.LayerDepth * 5
            
            # draw the rotated rectangle inner
            sketch = create_sketch(main_comp, 'angled-rectangles-inner', offset=layer_offset)            
            extrude_height = AppConfig.LayerDepth * 2
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
            for profile in sketch.profiles:
                extrude_thin_one(component=main_comp, profile=profile, extrudeHeight=extrude_height, strokeWeight=DiagonalRectangleConfig.InnerDiagonalRectangleStrokeWeight, name="angled-rectangles-inner", operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            # draw the astroid 32
            sketch = create_sketch(main_comp, 'astroid-32-outer', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius), extrude_height=extrude_height, name='astroid-32-outer',fp_tolerance=1e0)
            
            # layer 6D -----------
            layer_offset = AppConfig.LayerDepth * 6

            # draw the astroid 32 inner            
            sketch = create_sketch(main_comp, 'astroid-32-inner', offset=layer_offset)
            extrude_height = AppConfig.LayerDepth
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight, scaleY=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight)
            extrude_profile_by_area(component=main_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight), extrude_height=extrude_height, name='astroid-32-inner', fp_tolerance=1e-1)
           
        # Structural Component - Outer Brace
        if not component_exist(root_comp, create_component_name('core-outer-brace')):
            try:
                # Drawing a Outer Brace 
                width = AppConfig.MaxWidth
                length = AppConfig.MaxLength
                
                # depth repeat
                depth_repeat = 4
                
                # start layer offset
                start_layer_offset = AppConfig.LayerDepth * 2
                
                # Outer Brace
                outer_brace_comp = create_component(root_component=root_comp, component_name=create_component_name("core-outer-brace"))
                
                # draw the outer brace
                extrude_height_per_layer = AppConfig.LayerDepth * 4 / depth_repeat
                stroke_weight = 0.64 * ScaleConfig.ScaleFactor
                depth_repeat = 4
                
                for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset=start_layer_offset, extrude_height=extrude_height_per_layer, stroke_weight=stroke_weight):
                    sketch = create_sketch(outer_brace_comp, 'outer-brace' + str(layer_offset), offset=layer_offset)
                    draw_rectangle(sketch=sketch, length=length, width=width)
                    extrude_thin_one(component=outer_brace_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='outer-brace', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side1)
                
            except:
                log("core-outer-brace: none to draw")
            
        # Structural Component - Tesseract Projection
        # if not component_exist(root_comp, create_component_name('core-tesseract')):
        #     try:
        #         # Drawing a Tesseract structure
        #         tesseract_comp = create_component(root_component=root_comp, component_name=create_component_name("core-tesseract"))
            
        #         # depth repeat
        #         depth_repeat = 4
                
        #         # size
        #         size = (64.0) * ScaleConfig.ScaleFactor
                
        #         # extrude height
        #         max_height = AppConfig.LayerDepth * 4
        #         extrude_height_per_layer = (max_height) / depth_repeat
                
        #         # stroke weight
        #         stroke_weight = 0.64 * ScaleConfig.ScaleFactor
                
        #         # start layer offset
        #         start_layer_offset = AppConfig.LayerDepth * 2
                
        #         # depth effect
        #         for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight):
        #             # tesseract
        #             sketch = create_sketch(tesseract_comp, 'tesseract-inner-rect', offset=layer_offset)
        #             draw_tesseract_projection(sketch, center_x=0, center_y=0, size=size)

        #             # extrude
        #             for profile in sketch.profiles:
        #                 extrude_thin_one(component=tesseract_comp, profile=profile, extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='tesseract', operation=adsk.fusion.FeatureOperations.JoinFeatureOperation)
                        
        #             # # outer rect
        #             # sketch = create_sketch(tesseract_comp, 'tesseract-outer-rect', offset=layer_offset)
        #             # draw_rectangle(sketch=sketch, length=size, width=size)
        #             # extrude_thin_one(component=tesseract_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='tesseract-outer-rect', operation=adsk.fusion.FeatureOperations.JoinFeatureOperation, side=DepthEffect.Side2)
        #     except:
        #         log("tesseract: none to draw")
        # return
                
        # Structural Component - Interstellar Tesellation
        if not component_exist(root_comp, create_component_name('interstellar-tesellation')):
            interstellar_tesellation_comp = create_component(root_component=root_comp, component_name=create_component_name("interstellar-tesellation"))
            
            # draw from middle
            center_x = 0
            center_y = 0
            depth_repeat = 4
            extrude_height_per_layer = AppConfig.LayerDepth * 2 / depth_repeat
            stroke_weight = 0.64 * ScaleConfig.ScaleFactor
            start_layer_offset = AppConfig.LayerDepth * 3
           
            for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight): 
                sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-outer', offset=layer_offset)
                draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth, height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight)
                extrude_thin_one(component=interstellar_tesellation_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='interstellar-tesellation-outer', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
               
            # for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight): 
            #     sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-middle', offset=layer_offset)
            #     draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
            #     extrude_thin_one(component=interstellar_tesellation_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='interstellar-tesellation-middle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side2)
            
            # cut with AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea
            # sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-astroid-outer-cut', offset=AppConfig.LayerDepth)
            # draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
            # draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
            # extrude_profile_by_area(component=interstellar_tesellation_comp, profiles=sketch.profiles, area=KailashConfig.AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea, extrude_height=AppConfig.LayerDepth, name='interstellar-tesellation-astroid-outer-cut', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)

        if not component_exist(root_comp, create_component_name('layer-0-seed-of-life')):
            # top level comp
            seed_of_life_comp = create_component(root_component=root_comp, component_name=create_component_name("layer-0-seed-of-life"))
            
            # depth repeat
            depth_repeat = 4
            
            # extrude height
            extrude_height_per_layer = AppConfig.LayerDepth * 2 / depth_repeat
            
            # start layer offset
            start_layer_offset = AppConfig.LayerDepth * 2
            
            # iterate; the enumerator is an array of multiples of 8; e.g [8, 16, 24, 32, 40, 48, 56, 64]
            for (_, radius) in enumerate(create_array_random_unique_multiples(size=2, multiple=8 * ScaleConfig.ScaleFactor, min_multiple=4, max_multiple=10)):
                seed_of_life_layer_0_comp = create_component(root_component=seed_of_life_comp, component_name=create_component_name("seed-of-life-layer-0-" + str(radius)))
                
                # draw from middle
                center_x = 0
                center_y = 0
                
                
                # stroke weight
                stroke_weight = create_array_random_unique_multiples(size=1, multiple=0.48 * ScaleConfig.ScaleFactor, min_multiple=1, max_multiple=6)[0]
                
                # depth iterator
                for layer_offset, sw in depth_repeat_iterator(depth_repeat=depth_repeat, start_layer_offset=start_layer_offset, extrude_height=extrude_height_per_layer,stroke_weight=stroke_weight, direction=DepthRepeat.Decrement):
                    seed_of_life_layer_0_inner_comp = create_component(root_component=seed_of_life_layer_0_comp, component_name=create_component_name("seed-of-inner-layer-" + str(layer_offset) + "-" + str(sw)))
                    log(f"INIT seed-of-life-layer-0: depth-repeat 2, initial-radius: {radius}, extrude-height-per-layer: {extrude_height_per_layer}, stroke-weight: {sw}")
                    create_seed_of_life(root_component=seed_of_life_layer_0_inner_comp, center_x=center_x, center_y=center_y, radius=radius, extrude_height=extrude_height_per_layer, stroke_weight=sw, layer_offset=layer_offset, side=DepthEffect.Center)
                    # all_bodies.add(seed_of_life_inner_layer_comp.bRepBodies.item(0))
                    
                    # invert the joint body; re should always be in first occurance
                    invert_bodies = adsk.core.ObjectCollection.create()
                    invert_bodies.add(seed_of_life_layer_0_inner_comp.bRepBodies.item(0))
                    sketch = create_sketch(seed_of_life_layer_0_inner_comp, 'seed-of-life-inverse', offset=layer_offset)
                    draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
                    invert_body = extrude_single_profile_by_area(component=seed_of_life_layer_0_inner_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), extrude_height=extrude_height_per_layer, name='seed-of-life-inverse', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    combine_body(seed_of_life_layer_0_inner_comp, invert_body, invert_bodies, operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
        
        if not component_exist(root_comp, create_component_name('layer-0-torus')):
            try:
                torus_comp = create_component(root_component=root_comp, component_name=create_component_name("layer-0-torus"))
                
                # depth repeat
                depth_repeat = random.choice([2, 4])
                
                # extrude height
                extrude_height_per_layer = AppConfig.LayerDepth * 2 / depth_repeat
                
                # start layer offset
                start_layer_offset = AppConfig.LayerDepth * 2
                
                # iterate; the enumerator is an array of multiples of 8; e.g [8, 16, 24, 32, 40, 48, 56, 64]
                for (_, radius) in enumerate(create_array_random_unique_multiples(size=random.randint(1, 2), multiple=8 * ScaleConfig.ScaleFactor, min_multiple=8, max_multiple=16)):
                    torus_overlay_comp = create_component(root_component=torus_comp, component_name=create_component_name("torus-inner-" + str(radius)))
                    
                    # draw from middle
                    center_x = 0
                    center_y = 0
                    
                    
                    # stroke weight
                    stroke_weight = create_array_random_unique_multiples(size=1, multiple=0.48 * ScaleConfig.ScaleFactor, min_multiple=1, max_multiple=6)[0]
                    
                    # iterations random
                    # iterations = create_array_random_unique_multiples(size=1, multiple=16, min_multiple=8, max_multiple=32)[0]
                    iterations = random.choice([16, 32, 48])
                    
                    # depth iterator
                    for layer_offset, sw in depth_repeat_iterator(depth_repeat=depth_repeat, start_layer_offset=start_layer_offset, extrude_height=extrude_height_per_layer,stroke_weight=stroke_weight, direction=DepthRepeat.Decrement):
                        torus_overlay_inner_comp = create_component(root_component=torus_overlay_comp, component_name=create_component_name("torus-inner-" + str(radius) + "-" + str(sw)))
                        create_torus(root_component=torus_overlay_inner_comp, center_x=center_x, center_y=center_y, radius=radius, iterations=iterations, stroke_weight=sw, extrude_height=extrude_height_per_layer, layer_offset=layer_offset)
                        
                        # get all bodies
                        invert_bodies = adsk.core.ObjectCollection.create()
                        for body in torus_overlay_inner_comp.bRepBodies:
                            invert_bodies.add(body)
                        
                        # invert the joint body; re should always be in first occurance
                        sketch = create_sketch(torus_overlay_inner_comp, 'seed-of-life-inverse', offset=layer_offset)
                        draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
                        invert_body = extrude_single_profile_by_area(component=torus_overlay_inner_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), extrude_height=extrude_height_per_layer, name='seed-of-life-inverse', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                        combine_body(torus_overlay_inner_comp, invert_body, invert_bodies, operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
                
            except:
                log("torus-overlay: none to draw")
        
               
        if not component_exist(root_comp, create_component_name('torus')):
            torus_comp = create_component(root_component=root_comp, component_name=create_component_name("torus"))
           
            # inner torus
            iterations = 16
            radius = (24.0 - 1.28) * ScaleConfig.ScaleFactor
            stroke_weight = 0.64 * ScaleConfig.ScaleFactor
            inner_torus_component = create_component(root_component=torus_comp, component_name=create_component_name("torus-outer-" + str(radius) + "-" + str(iterations)))
            depth_repeat = 4
            start_layer_offset = AppConfig.LayerDepth * 3
            extrude_height_per_layer = AppConfig.LayerDepth / 2 / depth_repeat
            for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight, direction=DepthRepeat.Decrement):
                # create the torus
                seed_of_life_layer_0_inner_comp = create_component(root_component=inner_torus_component, component_name=create_component_name("torus-inner-" + str(radius) + "-" + str(sw)))
                create_torus(root_component=seed_of_life_layer_0_inner_comp, center_x=0, center_y=0, radius=radius, iterations=iterations, stroke_weight=sw, extrude_height=extrude_height_per_layer, layer_offset=layer_offset)
                
                # get all bodies
                invert_bodies = adsk.core.ObjectCollection.create()
                for body in seed_of_life_layer_0_inner_comp.bRepBodies:
                    invert_bodies.add(body)
                
                # invert the joint body; re should always be in first occurance
                sketch = create_sketch(torus_comp, 'torus-inverse', offset=layer_offset)
                draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight, scaleY=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight)
                invert_body = extrude_single_profile_by_area(component=torus_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight), extrude_height=extrude_height_per_layer, name='astroid-32-inner', fp_tolerance=1e-1)
                combine_body(torus_comp, invert_body, invert_bodies, operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
                
                # add astroid bracing (stroke)
                sketch = create_sketch(torus_comp, 'torus-astroid-bracing', offset=layer_offset)
                draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight, scaleY=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight, strokeWeight=0.64 * ScaleConfig.ScaleFactor)
                extrude_profile_by_area(component=torus_comp, profiles=sketch.profiles, area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight) - calculate_astroid_area(AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight - 0.64 * ScaleConfig.ScaleFactor), extrude_height=extrude_height_per_layer, name='torus-astroid-bracing', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                
            # combine all the bodies
            all_bodies = aggregate_all_bodies(torus_comp)
            root_body = all_bodies.item(0)
            all_bodies.removeByIndex(0)
            combine_body(torus_comp, root_body, all_bodies, operation=adsk.fusion.FeatureOperations.JoinFeatureOperation)

        try:
            middle_circle_comp = create_component(root_component=root_comp, component_name=create_component_name("middle_circle_comp"))
            
            sketch = create_sketch(middle_circle_comp, 'hole-thin-circle', offset=AppConfig.LayerDepth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_thin_one(component=middle_circle_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.LayerDepth * 4, strokeWeight=0.64 * ScaleConfig.ScaleFactor, name='hole-thin-circle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side1)
            
            sketch = create_sketch(middle_circle_comp, 'cut-hole', offset=AppConfig.LayerDepth)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_profile_by_area(component=middle_circle_comp, profiles=sketch.profiles, area=calculate_circle_area(AppConfig.HoleRadius), extrude_height=AppConfig.LayerDepth * 4, name='cut-hole', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
            
            # sketch = create_sketch(middle_circle_comp, 'inner-circle', offset=AppConfig.LayerDepth)
            # draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            # extrude_thin_one(component=middle_circle_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.LayerDepth * 2, strokeWeight=0.64 * ScaleConfig.ScaleFactor, name='inner-circle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side2)
            
            # sketch = create_sketch(middle_circle_comp, 'outer-circle', offset=AppConfig.LayerDepth)
            # draw_circle(sketch=sketch, radius=AppConfig.HoleRadius * 2)
            # extrude_thin_one(component=middle_circle_comp, profile=sketch.profiles[0], extrudeHeight=AppConfig.LayerDepth * 2, strokeWeight=0.64 * ScaleConfig.ScaleFactor, name='outer-circle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side1)
        except:
            log("cut-hole: none to cut")
            
        # Structural Component - Kailash Terrain Generation Sketch
        # Note: This is a placeholder for the actual terrain generation code. Requires manual intervention using STL files & Fusion Forms.
        # Guide: https://www.youtube.com/watch?v=Ea_YC4Jh0Sw
        try:
            kailash_comp = create_component(root_component=root_comp, component_name=create_component_name("cut-kailash-intersection"))
            sketch = create_sketch(kailash_comp, 'cut-kailash-intersection', offset=AppConfig.LayerDepth * 2 + AppConfig.LayerDepth / 2)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight)
            draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth, height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight)
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius)
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight, scaleY=AstroidConfig.OuterAstroidRadius - AstroidConfig.OuterAstroidStrokeWeight)
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius, scaleY=AstroidConfig.InnerAstroidRadius)
            draw_astroid(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight, scaleY=AstroidConfig.InnerAstroidRadius - AstroidConfig.InnerAstroidStrokeWeight)
            # for profile in sketch.profiles:
            #     log(f"cut-kailash-intersection: profile area: {profile.areaProperties().area}")
            extrude_profile_by_area(component=kailash_comp, profiles=sketch.profiles, area=KailashConfig.KailashIntersectExtrudeArea, extrude_height=AppConfig.LayerDepth, name='cut-kailash-intersection', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)
        except:
            log("cut-kailash-intersection: none to cut")
                
        # intersect only in bounds
        try:
            intersect_only_in_bounds_comp = create_component(root_component=root_comp, component_name=create_component_name("intersect-only-in-bounds"))
            sketch = create_sketch(intersect_only_in_bounds_comp, 'intersect-only-in-bounds', offset=AppConfig.LayerDepth)
            draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
            extrude_profile_by_area(component=intersect_only_in_bounds_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), extrude_height=AppConfig.LayerDepth * 2, name='intersect-only-in-bounds', operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation)
        except:
            log("intersect-only-in-bounds: none to cut")
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
  
@timer      
def slicer(root_component: adsk.fusion.Component,design: adsk.core.Product, sliced_layer_depth: float, sliced_layer_count: float):
    # Ensure design is set to parametric
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    
    # Create a new component for the slicing operation
    slicer_comp = create_component(root_component, create_component_name('slicer'))
    
    # Gather all bodies from the root component and its subcomponents
    all_bodies = aggregate_all_bodies(root_component)
    
    # Combine the rest of the bodies with the main body
    tool_bodies = adsk.core.ObjectCollection.create()
    for i in range(all_bodies.count):
        body_copy = copy_body(slicer_comp, all_bodies.item(i), 'slicer-body-' + str(i))
        tool_bodies.add(body_copy)
    
    # Perform the combination
    first_body = tool_bodies.item(0)
    tool_bodies.removeByIndex(0)
    combine_body(slicer_comp, first_body, tool_bodies, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    
    # rename
    first_body.name = 'slicer-body-root'
    
    # slice the body
    slice_body(slicer_comp, first_body, sliced_layer_depth, sliced_layer_count)

def aggregate_all_bodies(component: adsk.fusion.Component, all_bodies: adsk.core.ObjectCollection = None, depth_limit: int = -1):
    if all_bodies is None:
        all_bodies = adsk.core.ObjectCollection.create()
    
    # Add all bodies from the current component
    for body in component.bRepBodies:
        all_bodies.add(body)

    # Check if the depth limit has been reached
    if depth_limit == 0:
        return all_bodies

    # Recursively process all subcomponents, decreasing depth limit by 1 with each call
    for occurrence in component.occurrences:
        aggregate_all_bodies(occurrence.component, all_bodies, depth_limit - 1 if depth_limit > 0 else -1)

    return all_bodies
    
@timer
def slice_body(slicer_component: adsk.fusion.Component, body: adsk.fusion.BRepBody, sliced_layer_depth: float, sliced_layer_count: float):
    log(f"slice_body: body: {body.name}, sliced_layer_depth: {sliced_layer_depth}, sliced_layer_count: {sliced_layer_count}")
    
    # Get the bounding box of the body
    bounding_box = body.boundingBox
    min_point = bounding_box.minPoint
    max_point = bounding_box.maxPoint
    
    # Calculate the dimensions
    height = max_point.z - min_point.z
    
    # Calculate the number of slices and the height of each slice
    slice_height = sliced_layer_depth
    slice_count = int(min(sliced_layer_count, math.floor(height / slice_height)))
    
    # Log the details (assumed log function exists or use print instead)
    print(f"slice_body: height: {height}, slice_count: {slice_count}, slice_height: {slice_height}")
    
    # Iterate to create each slice
    for i in range(slice_count):
        # Calculate the offset for the current plane
        offset = min_point.z + ((i + 1) * slice_height)
        
        # Create an offset plane at the calculated position
        offset_plane = create_offset_plane(slicer_component, offset, name=f'plane-slice-{i}')
        
        # log
        log(f"slice_body: offset_plane: {offset_plane.name}, offset: {offset}")
        
        # Split the body using the created plane
        
        split_body_features = slicer_component.features.splitBodyFeatures
        split_body_input = split_body_features.createInput(body, offset_plane, True)
        newBodies = split_body_features.add(split_body_input).bodies
        
        # Get the new body
        slice_body = newBodies.item(0)
        slice_body.name = f'slice-body-{i}'
        
        # replace the original body with the new body
        body = newBodies.item(1)
        body.name = f'slice-body-remaining'
        
            
@timer
def create_seed_of_life(root_component: adsk.fusion.Component, center_x, center_y, radius, extrude_height, stroke_weight, layer_offset, side :adsk.fusion.ThinExtrudeWallLocation=adsk.fusion.ThinExtrudeWallLocation.Side1):
    # radius, stroke-weight, extrude-height difference each layer is based on j; gives it the "depth" effect
    r = radius
    sw = stroke_weight
    eh = extrude_height
    log(f"CREATE seed-of-life-inner: radius: {r} and stroke-weight: {sw} and extrude-height: {eh}")
   
    # draw the center circle
    sketch = create_sketch(root_component, 'seed-of-life-' + str(r) + '-center', layer_offset)
    draw_circle(sketch, r, center_x, center_y)
    initial_body = extrude_thin_one(component=root_component, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-center-' + str(r), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.JoinFeatureOperation)
    initial_body.name = 'seed-of-life-center-' + str(r)
    
    # draw; this is a standard seed of life algorithm.
    for i in range(6):
        # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
        angle = math.radians(i * 60)
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)

        # draw
        if AppConfig.DesignMode == DesignMode.DirectDesign:
            sketch = create_sketch(root_component, 'seed-of-life-' + str(r) + "-" + str(angle), layer_offset)
            draw_circle(sketch, r, x, y)
            extrude_thin_one(component=root_component, profile=sketch.profiles[0], extrudeHeight=eh, name='seed-of-life-' + str(r) + "-" + str(angle), strokeWeight=sw, operation=adsk.fusion.FeatureOperations.JoinFeatureOperation, side=side)        
        elif AppConfig.DesignMode == DesignMode.ParametricDesign:
            # @todo add depth effect using "side" param
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
    return f"{PrintType.get_attr_name(ScaleConfig.ScaleFactor).lower()}-{name}"