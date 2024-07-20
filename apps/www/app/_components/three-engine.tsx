"use client";

import { Environment, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { type EngineCoreSettings, EngineProvider } from "./three-engine-provider";
import { ThreeScene } from "./three-scene";
import Viewcube from "./viewcube";

interface ThreeEngineProps extends EngineCoreSettings {
  name: string;
}

const ThreeEngine: React.FC<ThreeEngineProps> = ({ resolution, constructionPlane }) => {
  return (
    <EngineProvider resolution={resolution} constructionPlane={constructionPlane}>
      <Canvas camera={{ position: [5, 5, 5], fov: 75 }}>
        <ambientLight intensity={0.5 * Math.PI} />
        <ThreeScene />
        <Viewcube />
        <OrbitControls />
        <Environment preset="city" />
      </Canvas>
    </EngineProvider>
  );
};

export default ThreeEngine;
