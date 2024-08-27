from core.geometry.composition import Composition
from core.geometry.shapes.rectangle import CenterRectangle


def run():
    composition = Composition(plane_offset=2.0)
    composition.add_geometry(
        # Difference(
        CenterRectangle(
            length=32.0,
            width=32.0,
            thickness=3.0,
            center_x=0.0,
            center_y=0.0,
        )
        # ).apply(
        #     Circle(
        #         radius=10.0,
        #         thickness=3.0,
        #         center_x=0.0,
        #         center_y=0.0,
        #     ),
        # )
    )

    # print data about composition
    print(str(composition))


# main start
if __name__ == "__main__":
    # run the script
    run()
