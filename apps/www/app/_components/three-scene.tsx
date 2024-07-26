"use client";

import { useEngine } from "./three-engine-provider";
import type ViewCubeController from "./viewcube/three-viewcube";
import CylinderWireframe from "./cylinder-wireframe";
import { useViewcubeSyncMovement } from "./viewcube/use-viewcube-sync-movement";

interface SceneProps {
  vcControllerRef: React.MutableRefObject<ViewCubeController | undefined>;
}

const ThreeScene: React.FC<SceneProps> = ({ vcControllerRef: viewCubeControllerRef }) => {
  const { resolution, constructionPlane } = useEngine();
  const L = 10;
  const H = 4;
  const R = 1;

  // sync camera movement with viewcube
  useViewcubeSyncMovement({ viewCubeControllerRef });

  return <CylinderWireframe L={L} H={H} R={R} resolution={resolution} position={[0, H / 2, 0]} plane={constructionPlane} />;
};

export default ThreeScene;
