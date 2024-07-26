"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { type EngineCoreSettings, EngineProvider } from "./three-engine-provider";
import ThreeScene from "./three-scene";
import { useRef } from "react";
import type ViewCubeController from "./three-viewcube";
import Viewcube from "./viewcube";

interface ThreeEngineProps extends EngineCoreSettings {
  name: string;
}

const ThreeEngine: React.FC<ThreeEngineProps> = ({ resolution, constructionPlane }) => {
  const vcControllerRef = useRef<ViewCubeController>();

  return (
    <EngineProvider resolution={resolution} constructionPlane={constructionPlane}>
      <Canvas
        camera={{
          position: [10, 20, 20],
          zoom: 40,
          // left: -window.innerWidth / 2,
          // right: window.innerWidth / 2,
          // top: window.innerHeight / 2,
          // bottom: -window.innerHeight / 2,
        }}
        orthographic
      >
        <ThreeScene vcControllerRef={vcControllerRef} />
        <ambientLight intensity={0.1} />
        <directionalLight color="red" position={[0, 0, 5]} />
        <OrbitControls enableDamping={false} />
      </Canvas>
      <Viewcube vcControllerRef={vcControllerRef} />
    </EngineProvider>
  );
};

export default ThreeEngine;
