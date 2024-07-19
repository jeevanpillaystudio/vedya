import { type Vec3, type Mat4 } from "./_types";

export function createIdentityMatrix(): Mat4 {
  // prettier-ignore
  return [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
  ];
}

export function createTranslationMatrix(x: number, y: number, z: number): Mat4 {
  // prettier-ignore
  return [
    1, 0, 0, x,
    0, 1, 0, y,
    0, 0, 1, z,
    0, 0, 0, 1,
  ];
}

export function createRotationMatrixX(theta: number): Mat4 {
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  // prettier-ignore
  return [
    1, 0, 0, 0,
    0, c, -s, 0,
    0, s, c, 0,
    0, 0, 0, 1,
  ];
}

export function createRotationMatrixY(theta: number): Mat4 {
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  // prettier-ignore
  return [
    c, 0, s, 0,
    0, 1, 0, 0,
    -s, 0, c, 0,
    0, 0, 0, 1,
  ];
}

export function createRotationMatrixZ(theta: number): Mat4 {
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  // prettier-ignore
  return [
    c, -s, 0, 0,
    s, c, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
  ];
}

export function multiplyMatrices(a: Mat4, b: Mat4): Mat4 {
  // prettier-ignore
  const result: Mat4 = [
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0,
  ];

  // run through rows, columns, and inner matrix
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 4; col++) {
      let sum = 0;
      for (let k = 0; k < 4; k++) {
        sum += a[row * 4 + k]! * b[k * 4 + col]!;
      }
      result[row * 4 + col] = sum;
    }
  }

  return result;
}

export function multiplyMatrixAndPoint(matrix: Mat4, point: Vec3): Vec3 {
  const [x, y, z] = point;
  const w = 1;
  // prettier-ignore
  return [
      matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12] * w,
      matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13] * w,
      matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14] * w,
    ];
}
