from core.geometry.composition import Composition
from core.geometry.shapes.circle import Circle
from core.geometry.shapes.rectangle import Rectangle


def run():
    geometries = [
        Rectangle(length=32.0, width=32.0, thickness=3.0, parent=None),
        Circle(radius=16.0, thickness=3.0, parent=None)
    ]
    
    composition = Composition(geometries=geometries)
    
    # print data about composition
    print(str(composition))

# main start
if __name__ == "__main__":
    # run the script
    run()