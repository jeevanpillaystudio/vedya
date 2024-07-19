import { ConstructionPlane } from "./_enums";
import { type Vec2, type Mat4, type Vec3 } from "./_types";
import { createIdentityMatrix, createRotationMatrixX, createRotationMatrixY, multiplyMatrixAndPoint } from "./matrix";

type TransformFn = (point: Vec2, L: number, H: number, R?: number, rotationMatrix?: Mat4) => Vec3;

const rotationMatrices: { [key in ConstructionPlane]: Mat4 } = {
  [ConstructionPlane.XY]: createIdentityMatrix(), // No rotation needed for XY plane
  [ConstructionPlane.XZ]: createRotationMatrixX(Math.PI / 2), // Rotate around the X-axis for XZ plane
  [ConstructionPlane.YZ]: createRotationMatrixY(Math.PI / 2), // Rotate around the Y-axis for YZ plane
};

const cylinderTransform: (point: Vec2, L: number, R: number) => Vec3 = ([x, y], L, R) => {
  const theta = (2 * Math.PI * x) / L;
  const xPrime = R * Math.cos(theta);
  const yPrime = R * Math.sin(theta);
  return [xPrime, yPrime, y];
};

export function createCylinderPoints(
  L: number,
  H: number,
  R: number,
  resolution: number,
  plane: ConstructionPlane = ConstructionPlane.XY,
): Float32Array {
  const rotationMatrix = rotationMatrices[plane];

  const transformFn: TransformFn = (point, L, H, R, rotationMatrix) => {
    const [xPrime, yPrime, zPrime] = cylinderTransform(point, L, R!);
    return multiplyMatrixAndPoint(rotationMatrix!, [xPrime, yPrime, zPrime]);
  };

  return createPoints(L, H, resolution, transformFn, R, rotationMatrix);
}

function createPoints(L: number, H: number, resolution: number, transformFn: TransformFn, R?: number, rotationMatrix?: Mat4): Float32Array {
  const xSteps = Math.floor(L / resolution);
  const ySteps = Math.floor(H / resolution);

  const points = new Float32Array(xSteps * ySteps * 3);
  let idx = 0;

  for (let i = 0; i < xSteps; i++) {
    const x = i * resolution;

    for (let j = 0; j < ySteps; j++) {
      const y = j * resolution;
      const point: Vec2 = [x, y];
      const [xPrime, yPrime, zPrime] = transformFn(point, L, H, R, rotationMatrix);
      points[idx++] = xPrime;
      points[idx++] = yPrime;
      points[idx++] = zPrime;
    }
  }

  return points;
}
