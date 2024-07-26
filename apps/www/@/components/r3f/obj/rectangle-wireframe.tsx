import React from "react";
import { type PointsProps } from "@react-three/fiber";
import { generateRectanglePoints } from "../_lib/transform-future-change";
import { DEFAULT_POINT_SIZE, DEFAULT_RESOLUTION } from "../_defaults";

interface RectangleWireframeProps extends PointsProps {
  L: number;
  H: number;
  color?: string;
  resolution?: number;
}

export const RectangleWireframe: React.FC<RectangleWireframeProps> = ({
  L,
  H,
  resolution = DEFAULT_RESOLUTION,
  color = "red",
  ...props
}) => {
  const rectangularPoints = generateRectanglePoints(L, H, resolution);
  return (
    <points {...props}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={rectangularPoints.length / 3} array={rectangularPoints} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={DEFAULT_POINT_SIZE} color={color} />
    </points>
  );
};

export default RectangleWireframe;
