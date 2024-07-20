"use client";

import { useFrame, useLoader, useThree } from "@react-three/fiber";
import CylinderWireframe from "./cylinder-wireframe";
import { useEngine } from "./three-engine-provider";
import { useEffect } from "react";
import ViewCubeController from "./three-viewcube";
import { getCameraCSSMatrix } from "./math";
import { Matrix4, Vector3 } from "three";
import { STLLoader } from "three/examples/jsm/Addons.js";

interface SceneProps {
  viewCubeControllerRef: React.MutableRefObject<ViewCubeController | undefined>;
}

function useModel() {
  const stl = useLoader(STLLoader, "teapot.stl");
  stl.lookAt(new Vector3(0, 1, 0));
  stl.translate(0, -3, 0);
  return stl;
}

const Scene: React.FC<SceneProps> = ({ viewCubeControllerRef }) => {
  const { camera } = useThree();

  const stl = useModel();

  useEffect(() => {
    if (!viewCubeControllerRef.current) {
      viewCubeControllerRef.current = new ViewCubeController(camera);
    }
  }, [camera, viewCubeControllerRef]);

  const L = 10;
  const H = 4;
  const R = 1;
  const { resolution, constructionPlane } = useEngine();

  const cube = document.querySelector(".cube");
  const matrix = new Matrix4();

  useFrame((state, delta, xrFrame) => {
    if (cube && camera) {
      matrix.extractRotation(camera.matrixWorldInverse);
      (cube as HTMLElement).style.transform = `translateZ(-300px) ${getCameraCSSMatrix(matrix)}`;
    }

    if (viewCubeControllerRef.current) {
      viewCubeControllerRef.current.tweenCallback();
    }
  });

  return (
    <>
      <mesh>
        <primitive object={stl} scale={0.01} />
        <meshStandardMaterial color="hotpink" />
      </mesh>
      {/* <CylinderWireframe L={L} H={H} R={R} resolution={resolution} position={[0, H / 2, 0]} plane={constructionPlane} />; */}
    </>
  );
};

export default Scene;
