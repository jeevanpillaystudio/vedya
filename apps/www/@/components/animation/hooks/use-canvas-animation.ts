import { type UpdateFunction, type RenderFunction } from "../types";
import { useAnimationControls } from "./use-animation-controls";
import { useAnimationLoop } from "./use-animation-loop";
import { useCanvasResize } from "./use-canvas-resize";

/**
 * A custom hook that manages canvas animation with integrated debugging capabilities.
 * 
 * This hook combines several smaller hooks to create a complete animation system:
 * - useAnimationLoop: Handles the core animation loop logic
 * - useCanvasResize: Manages canvas resizing
 * - useAnimationControls: Provides start, stop, and restart functionality
 * 
 * @param updateFn - Function to update the animation state each frame
 * @param renderFn - Function to render the animation on the canvas each frame
 * 
 * @returns An object containing:
 *   - canvasRef: Ref to be attached to the canvas element
 *   - startAnimation: Function to start the animation
 *   - stopAnimation: Function to stop the animation
 */
export const useCanvasAnimation = (updateFn: UpdateFunction, renderFn: RenderFunction) => {
  // Set up the core animation loop
  const { canvasRef, animationRef, stateRef, gameLoop, reset } = useAnimationLoop(updateFn, renderFn);

  // Set up canvas resizing
  useCanvasResize(canvasRef);

  // Set up animation controls
  const { startAnimation, stopAnimation } = useAnimationControls(animationRef, stateRef, gameLoop);

  return { canvasRef, startAnimation, stopAnimation, reset };
};