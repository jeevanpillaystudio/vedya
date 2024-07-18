"use client";

import React from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import CylinderWireframe from "./cylinder-wireframe";
import RectangleWireframe from "./rectangle-wireframe";
import CuboidWireframe from "./cuboid-wireframe";

const ThreeScene: React.FC = () => {
  const L = 10;
  const W = 4;
  const H = 4;
  const R = 1;
  const cylinderResolution = 0.1;

  return (
    <Canvas camera={{ position: [5, 5, 5], fov: 75 }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <CylinderWireframe
        L={L}
        H={H}
        R={R}
        resolution={cylinderResolution}
        position={[0, H / 2, 0]}
      />
      {/* <RectangleWireframe
        L={L}
        H={H}
        resolution={cylinderResolution}
        position={[0, 0, 0]}
      /> */}
      <CuboidWireframe
        L={L}
        W={W}
        H={H}
        resolution={cylinderResolution}
        position={[0, 0, 0]}
      />
      <mesh position={[0, H / 2, 0]}>
        <cylinderGeometry args={[R, R, H, 32]} />
        <meshStandardMaterial
          wireframe
          color="blue"
          opacity={0.3}
          transparent
        />
      </mesh>
      <OrbitControls
        enableDamping
        dampingFactor={0.25}
        rotateSpeed={0.5}
        maxPolarAngle={Math.PI / 2}
        minPolarAngle={0}
      />
    </Canvas>
  );
};

export default ThreeScene;
