from core.geometry.composition import Composition
from core.geometry.composition_geometry import CompositionGeometry
from core.geometry.shapes.circle import Circle
from core.geometry.shapes.rectangle import Rectangle

def Difference(shape1: CompositionGeometry, shape2: CompositionGeometry) -> CompositionGeometry:
    return shape1

def run():
    composition = Composition(plane_offset=2.0)
    composition.add_geometry(
        Difference(
        shape1=Rectangle(
            length=32.0,
            width=32.0,
            thickness=3.0,
            center_x=0.0,
            center_y=0.0,
        ),
        shape2=Circle(
            radius=10.0,
            thickness=3.0,
            center_x=0.0,
            center_y=0.0,
        )),
        plane_offset=2.0
    )
    
    # print data about composition
    print(str(composition))

# main start
if __name__ == "__main__":
    # run the script
    run()