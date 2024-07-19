"use client";

import CylinderWireframe from "./cylinder-wireframe";
import { useEngine } from "./three-engine-provider";

const ThreeScene: React.FC = () => {
  const L = 10;
  const H = 4;
  const R = 1;
  const { resolution, constructionPlane } = useEngine();
  return (
    <>
      <CylinderWireframe L={L} H={H} R={R} resolution={resolution} position={[0, H / 2, 0]} plane={constructionPlane} />;
    </>
  );
};

export { ThreeScene };
