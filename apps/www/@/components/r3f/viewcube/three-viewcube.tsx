import { Vector3, type Camera } from "three";

export type Orientation = {
  offsetFactor: {
    x: number;
    y: number;
    z: number;
  };
  rotationX: number;
  rotationY: number;
};

class ViewCubeController {
  static CubeOrientation = {
    Top: "top",
    Bottom: "bottom",
    Front: "front",
    Back: "back",
    Left: "left",
    Right: "right",
  };

  static ORIENTATIONS: Record<string, Orientation> = {
    top: {
      offsetFactor: { x: 0, y: 1, z: 0 },
      rotationX: 90,
      rotationY: 0,
    },
    bottom: {
      offsetFactor: { x: 0, y: -1, z: 0 },
      rotationX: -90,
      rotationY: 0,
    },
    front: {
      offsetFactor: { x: 0, y: 0, z: 1 },
      rotationX: 0,
      rotationY: 0,
    },
    back: {
      offsetFactor: { x: 0, y: 0, z: -1 },
      rotationX: 0,
      rotationY: 180,
    },
    left: {
      offsetFactor: { x: -1, y: 0, z: 0 },
      rotationX: 0,
      rotationY: -90,
    },
    right: {
      offsetFactor: { x: 1, y: 0, z: 0 },
      rotationX: 0,
      rotationY: 90,
    },
  };

  private camera: Camera;

  constructor(camera: Camera) {
    this.camera = camera;
  }

  animateCameraToOrientation(orientation: Orientation) {
    const { offsetFactor } = orientation;

    if (this.camera) {
      const offsetUnit = this.camera.position.length();
      const offset = new Vector3(offsetUnit * offsetFactor.x, offsetUnit * offsetFactor.y, offsetUnit * offsetFactor.z);

      const center = new Vector3();
      const finishPosition = center.add(offset);

      // The target position the camera should always look at
      const targetPosition = new Vector3(0, 0, 0);

      this.animateCamera(this.camera.position, finishPosition, 300, () => {
        this.camera.lookAt(targetPosition);
      });
    }
  }

  private animateCamera(startPosition: Vector3, endPosition: Vector3, duration: number, onUpdate: () => void) {
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsedTime = currentTime - startTime;
      const t = Math.min(elapsedTime / duration, 1);

      // Cubic ease-in-out
      const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

      const easedT = easeInOutCubic(t);

      this.camera.position.lerpVectors(startPosition, endPosition, easedT);
      onUpdate();

      if (t < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }
}

export default ViewCubeController;
