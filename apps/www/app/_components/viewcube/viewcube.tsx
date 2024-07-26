// @todo refactor styles to clsx

import { type MutableRefObject } from "react";
import ViewCubeController from "./three-viewcube";
import { cn } from "../../_react/css-utils";

interface ViewcubeInterface {
  vcControllerRef: MutableRefObject<ViewCubeController | undefined>;
}

const Viewcube: React.FC<ViewcubeInterface> = ({ vcControllerRef }) => {
  return (
    <div
      id="viewcube-container"
      className={cn("perspective-[600px] absolute bottom-[40px] right-[60px] z-[2] m-[10px] h-[120px] w-[120px]")}
    >
      <div
        id="cube"
        className="cube preserve-3d relative h-[100px] w-[100px]"
        style={{ transformStyle: "preserve-3d", transform: "translateZ(-300px)" }}
      >
        {Object.values(ViewCubeController.CubeOrientation).map((orientation) => (
          <div
            key={orientation}
            className={cn(
              `cube__face cube__face--${orientation}`,
              "absolute left-0 top-0 flex h-[100px] w-[100px] cursor-pointer select-none items-center justify-center border-2 border-gray-400 bg-white text-2xl font-bold text-gray-600",
            )}
            style={{
              transform: `rotateX(${ViewCubeController.ORIENTATIONS[orientation]!.rotationX}deg) rotateY(${ViewCubeController.ORIENTATIONS[orientation]!.rotationY}deg) translateZ(50px)`,
            }}
            onClick={() => {
              if (!vcControllerRef.current) {
                return;
              }
              vcControllerRef.current.tweenCamera(ViewCubeController.ORIENTATIONS[orientation]!);
            }}
          >
            {orientation}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Viewcube;
