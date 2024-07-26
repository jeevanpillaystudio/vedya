import React from "react";
import { generateCuboidPoints } from "../_lib/transform-future-change";
import { type PointsProps } from "@react-three/fiber";
import { DEFAULT_POINT_SIZE, DEFAULT_RESOLUTION } from "../_defaults";
import { type Color } from "@react-three/fiber";

interface CuboidWireframeProps extends PointsProps {
  L: number;
  W: number;
  H: number;
  color?: Color;
  resolution?: number;
}

const CuboidWireframe: React.FC<CuboidWireframeProps> = ({ L, H, W, resolution = DEFAULT_RESOLUTION, color = "red", ...props }) => {
  const cuboidPoints = generateCuboidPoints(L, W, H, resolution);
  return (
    <points {...props}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={cuboidPoints.length / 3} array={cuboidPoints} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={DEFAULT_POINT_SIZE} color={color} />
    </points>
  );
};

export default CuboidWireframe;
