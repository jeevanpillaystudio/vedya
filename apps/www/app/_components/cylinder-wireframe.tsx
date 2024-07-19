"use client";

import React from "react";
import type { Color, PointsProps } from "@react-three/fiber";
import { DEFAULT_CONSTRUCTION_PLANE, DEFAULT_POINT_SIZE, DEFAULT_RESOLUTION, DEFAULT_WIREFRAME_COLOR } from "./_defaults";
import { type ConstructionPlane } from "../_lib/_enums";
import { createCylinderPoints } from "../_lib/transform";

interface CylinderWireframeProps extends PointsProps {
  L: number;
  H: number;
  R: number;
  resolution: number;
  plane: ConstructionPlane;
  color?: Color;
}

const CylinderWireframe: React.FC<CylinderWireframeProps> = ({
  L,
  H,
  R,
  resolution = DEFAULT_RESOLUTION,
  color = DEFAULT_WIREFRAME_COLOR,
  plane = DEFAULT_CONSTRUCTION_PLANE,
  ...props
}) => {
  const cylinderPoints = createCylinderPoints(L, H, R, resolution, plane);
  return (
    <points {...props}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={cylinderPoints.length / 3} array={cylinderPoints} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={DEFAULT_POINT_SIZE} color={color} />
    </points>
  );
};

export default CylinderWireframe;
