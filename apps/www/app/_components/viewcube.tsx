// @todo refactor styles to clsx

import { type MutableRefObject } from "react";
import ViewCubeController from "./three-viewcube";

interface ViewcubeInterface {
  vcControllerRef: MutableRefObject<ViewCubeController | undefined>;
}

const Viewcube: React.FC<ViewcubeInterface> = ({ vcControllerRef }) => {
  return (
    <div
      id="viewcube-container"
      style={{
        width: "120px",
        height: "120px",
        margin: "10px",
        perspective: "600px",
        position: "absolute",
        right: "60px",
        bottom: "40px",
        zIndex: 2,
      }}
    >
      <div
        id="cube"
        className="cube"
        style={{ width: "100px", height: "100px", position: "relative", transformStyle: "preserve-3d", transform: "translateZ(-300px)" }}
      >
        {Object.values(ViewCubeController.CubeOrientation).map((orientation) => (
          <div
            key={orientation}
            className={`cube__face cube__face--${orientation}`}
            style={{
              width: "100px",
              height: "100px",
              border: "2px solid #808080",
              lineHeight: "100px",
              fontSize: "25px",
              fontWeight: "bold",
              color: "#7d7d7d",
              textAlign: "center",
              background: "#fff",
              cursor: "pointer",
              userSelect: "none",
              position: "absolute",
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