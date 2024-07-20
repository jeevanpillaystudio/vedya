"use client";

import React, { useRef, forwardRef, useImperativeHandle } from "react";
import { Hud, OrthographicCamera, RenderTexture, Text } from "@react-three/drei";
import { useThree, useFrame, type MeshProps } from "@react-three/fiber";
import { type Mesh, Matrix4 } from "three";

const Viewcube: React.FC = () => {
  const renderPriority = 1;
  const matrix = new Matrix4();
  const mesh = useRef<Mesh>(null);
  const { camera } = useThree();

  useFrame(() => {
    // Spin mesh to the inverse of the default camera's matrix
    matrix.copy(camera.matrix).invert();

    if (mesh.current) {
      mesh.current.quaternion.setFromRotationMatrix(matrix);
    }
  });

  return (
    <Hud renderPriority={renderPriority}>
      <Box ref={mesh} position={[0, 0, 0]}>
        <ViewcubeFace index={0}>FRONT</ViewcubeFace>
        <ViewcubeFace index={1}>BACK</ViewcubeFace>
        <ViewcubeFace index={2}>TOP</ViewcubeFace>
        <ViewcubeFace index={3}>BOTTOM</ViewcubeFace>
        <ViewcubeFace index={4}>LEFT</ViewcubeFace>
        <ViewcubeFace index={5}>RIGHT</ViewcubeFace>
      </Box>
    </Hud>
  );
};

export default Viewcube;

interface BoxProps extends MeshProps {
  children: React.ReactNode;
}

const Box = forwardRef<Mesh, BoxProps>(({ children, ...props }, ref) => {
  const meshRef = useRef<Mesh>(null);
  useImperativeHandle(ref, () => meshRef.current!);
  return (
    <mesh {...props} ref={meshRef}>
      <boxGeometry args={[1, 1, 1]} />
      {children}
    </mesh>
  );
});

Box.displayName = "ViewcubeBox";

interface FaceMaterialProps {
  index: number;
  children: React.ReactNode;
}

const ViewcubeFace: React.FC<FaceMaterialProps> = ({ children, index }) => {
  return (
    <meshStandardMaterial attach={`material-${index}`} color={"orange"}>
      <RenderTexture attach="map" anisotropy={16}>
        <OrthographicCamera makeDefault position={[0, 0, 5]} zoom={50} />
        <Text fontSize={0.4} color="black" anchorX="center" anchorY="middle">
          {children}
        </Text>
      </RenderTexture>
    </meshStandardMaterial>
  );
};
