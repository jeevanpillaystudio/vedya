import { ConstructionPlane } from "./_enums";
import { type Mat4, type Vec3 } from "./_types";
import { createIdentityMatrix, createRotationMatrixX, createRotationMatrixY, multiplyMatrixAndPoint } from "./matrix";

type TransformFn = (x: number, y: number, L: number, H: number, R?: number, rotationMatrix?: Mat4) => Vec3;

const rotationMatrices: { [key in ConstructionPlane]: Mat4 } = {
  [ConstructionPlane.XY]: createIdentityMatrix(), // No rotation needed for XY plane
  [ConstructionPlane.XZ]: createRotationMatrixX(Math.PI / 2), // Rotate around the X-axis for XZ plane
  [ConstructionPlane.YZ]: createRotationMatrixY(Math.PI / 2), // Rotate around the Y-axis for YZ plane
};

const cylinderTransform: (x: number, y: number, L: number, R: number) => Vec3 = (x, y, L, R) => {
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

  const transformFn: TransformFn = (x, y, L, H, R, rotationMatrix) => {
    const [xPrime, yPrime, zPrime] = cylinderTransform(x, y, L, R!);
    return multiplyMatrixAndPoint(rotationMatrix!, [xPrime, yPrime, zPrime]);
  };

  return createPoints(L, H, resolution, transformFn, R, rotationMatrix);
}

export function transformToRectangle(x: number, y: number): [number, number, number] {
  return [x, y, 0];
}

export function transformToCylinder(x: number, y: number, L: number, R: number): [number, number, number] {
  const theta = (2 * Math.PI * x) / L;
  const xPrime = R * Math.cos(theta);
  const yPrime = R * Math.sin(theta);
  const zPrime = y;
  return [xPrime, yPrime, zPrime];
}

export function transformToSphere(x: number, y: number, L: number, H: number, R: number): [number, number, number] {
  const theta = (2 * Math.PI * x) / L;
  const phi = (Math.PI * y) / H;
  const xPrime = R * Math.sin(phi) * Math.cos(theta);
  const yPrime = R * Math.sin(phi) * Math.sin(theta);
  const zPrime = R * Math.cos(phi);
  return [xPrime, yPrime, zPrime];
}

export function generateRectanglePoints(L: number, H: number, resolution: number): Float32Array {
  const xSteps = Math.floor(L / resolution);
  const ySteps = Math.floor(H / resolution);

  const points = new Float32Array(xSteps * ySteps * 3);
  let idx = 0;

  for (let i = 0; i < xSteps; i++) {
    const x = i * resolution;

    for (let j = 0; j < ySteps; j++) {
      const y = j * resolution;
      const [xPrime, yPrime, zPrime] = transformToRectangle(x, y);
      points[idx++] = xPrime;
      points[idx++] = yPrime;
      points[idx++] = zPrime;
    }
  }

  return points;
}

export function generateSpherePoints(L: number, H: number, R: number, resolution: number): Float32Array {
  const xSteps = Math.floor(L / resolution);
  const ySteps = Math.floor(H / resolution);

  const points = new Float32Array(xSteps * ySteps * 3);
  let idx = 0;

  for (let i = 0; i < xSteps; i++) {
    const x = i * resolution;

    for (let j = 0; j < ySteps; j++) {
      const y = j * resolution;
      const [xPrime, yPrime, zPrime] = transformToSphere(x, y, L, H, R);
      points[idx++] = xPrime;
      points[idx++] = yPrime;
      points[idx++] = zPrime;
    }
  }

  return points;
}

export function transformToCuboidFace(x: number, y: number, L: number, W: number, H: number, face: string): [number, number, number] {
  switch (face) {
    case "front":
      return [x, y, 0];
    case "back":
      return [x, y, H];
    case "left":
      return [0, y, x];
    case "right":
      return [L, y, x];
    case "top":
      return [x, 0, y];
    case "bottom":
      return [x, W, y];
    default:
      throw new Error("Invalid face");
  }
}

export function generateCuboidPoints(L: number, W: number, H: number, resolution: number): Float32Array {
  const faces = ["front", "back", "left", "right", "top", "bottom"];
  let totalPoints = 0;

  for (const face of faces) {
    const xSteps = Math.floor((face === "left" || face === "right" ? H : L) / resolution);
    const ySteps = Math.floor((face === "top" || face === "bottom" ? H : W) / resolution);
    totalPoints += xSteps * ySteps * 3;
  }

  const points = new Float32Array(totalPoints);
  let idx = 0;

  for (const face of faces) {
    const xSteps = Math.floor((face === "left" || face === "right" ? H : L) / resolution);
    const ySteps = Math.floor((face === "top" || face === "bottom" ? H : W) / resolution);

    for (let i = 0; i < xSteps; i++) {
      const x = i * resolution;

      for (let j = 0; j < ySteps; j++) {
        const y = j * resolution;
        const [xPrime, yPrime, zPrime] = transformToCuboidFace(x, y, L, W, H, face);
        points[idx++] = xPrime;
        points[idx++] = yPrime;
        points[idx++] = zPrime;
      }
    }
  }

  return points;
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
      const [xPrime, yPrime, zPrime] = transformFn(x, y, L, H, R, rotationMatrix);
      points[idx++] = xPrime;
      points[idx++] = yPrime;
      points[idx++] = zPrime;
    }
  }

  return points;
}
