export function transformToCylinder(x: number, y: number, L: number, R: number): [number, number, number] {
    const theta = (2 * Math.PI * x) / L;
    const xPrime = R * Math.cos(theta);
    const yPrime = R * Math.sin(theta);
    const zPrime = y;
    return [xPrime, yPrime, zPrime];
  }
  
  export function transformRectangleToCylinder(L: number, H: number, R: number, resolution: number): Float32Array {
    const xSteps = Math.floor(L / resolution);
    const ySteps = Math.floor(H / resolution);
  
    const points = new Float32Array(xSteps * ySteps * 3); // Use Float32Array directly
    let idx = 0;
    for (let i = 0; i < xSteps; i++) {
      const x = i * resolution;
      const theta = (2 * Math.PI * x) / L; // Pre-compute theta for all y-values at this x
      const cosTheta = Math.cos(theta);
      const sinTheta = Math.sin(theta);
  
      for (let j = 0; j < ySteps; j++) {
        const y = j * resolution;
        points[idx++] = R * cosTheta;
        points[idx++] = y;
        points[idx++] = R * sinTheta;
      }
    }
  
    return points;
  }
  
  