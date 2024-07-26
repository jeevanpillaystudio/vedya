import { useFrame, useThree } from "@react-three/fiber";
import { useEffect } from "react";
import { Matrix4 } from "three";
import { getCameraCSSMatrix } from "../math";
import ViewCubeController from "./three-viewcube";

interface ViewCubeSyncMovementProps {
  viewCubeControllerRef: React.MutableRefObject<ViewCubeController | undefined>;
}

export const useViewcubeSyncMovement = ({ viewCubeControllerRef }: ViewCubeSyncMovementProps) => {
  const { camera } = useThree();
  const cube = document.querySelector(".cube");
  const matrix = new Matrix4();

  useEffect(() => {
    if (!viewCubeControllerRef.current) {
      viewCubeControllerRef.current = new ViewCubeController(camera);
    }
  }, [camera, viewCubeControllerRef]);

  useFrame(() => {
    if (cube && camera) {
      matrix.extractRotation(camera.matrixWorldInverse);
      (cube as HTMLElement).style.transform = `translateZ(-300px) ${getCameraCSSMatrix(matrix)}`;
    }
  });

  return {
    cube,
    matrix,
  };
};
