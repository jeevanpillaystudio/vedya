'use client';

import React from 'react';
import { Canvas } from '@react-three/fiber';
import ThreeCylinder from './three-cylinder';

const ThreeScene: React.FC = () => {
  const L = 10;
  const H = 4;
  const R = 1;
  const cylinderResolution = 0.1;

  return (
    <Canvas camera={{ position: [5, 5, 5], fov: 75 }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <ThreeCylinder L={L} H={H} R={R} cylinderResolution={cylinderResolution} />
      <mesh position={[0, H / 2, 0]}>
        <cylinderGeometry args={[R, R, H, 32]} />
        <meshStandardMaterial color="blue" opacity={0.3} transparent />
      </mesh>
    </Canvas>
  );
};


export default ThreeScene;
