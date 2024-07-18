import React from "react";
import { generateCylinderPoints } from "../_lib/transform";
import { type PointsProps } from "@react-three/fiber";
import { DEFAULT_POINT_SIZE, DEFAULT_RESOLUTION } from "./_defaults";
import { type Color } from "@react-three/fiber";

interface CylinderWireframeProps extends PointsProps {
  L: number;
  H: number;
  R: number;
  color?: Color;
  resolution?: number;
}

const CylinderWireframe: React.FC<CylinderWireframeProps> = ({
  L,
  H,
  R,
  resolution = DEFAULT_RESOLUTION,
  color = "red",
  ...props
}) => {
  const cylinderPoints = generateCylinderPoints(L, H, R, resolution);
  return (
    <points {...props}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={cylinderPoints.length / 3}
          array={cylinderPoints}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={DEFAULT_POINT_SIZE} color={color} />
    </points>
  );
};

export default CylinderWireframe;
