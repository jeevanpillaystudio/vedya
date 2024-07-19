"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { EngineProvider } from "./three-engine-provider";
import { ThreeScene } from "./three-scene";
import { type ConstructionPlane } from "../_lib/_enums";

interface ThreeEngineProps {
  resolution: number;
  constructionPlane: ConstructionPlane;
}

const ThreeEngine: React.FC<ThreeEngineProps> = ({ resolution, constructionPlane }) => {
  return (
    <EngineProvider resolution={resolution} constructionPlane={constructionPlane}>
      <Canvas camera={{ position: [5, 5, 5], fov: 75 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <ThreeScene />
        <OrbitControls enableDamping dampingFactor={0.25} rotateSpeed={0.5} maxPolarAngle={Math.PI / 2} minPolarAngle={0} />
      </Canvas>
    </EngineProvider>
  );
};

export default ThreeEngine;
