import { type UpdateFunction, type RenderFunction } from "../types";
import { useCanvasResize } from "../shared/use-canvas-resize";
import { useFrameManagement } from "../frame/use-frame-management";
import { useAnimationLoop } from "./use-animation-loop";

export const useCanvasAnimation = (updateFn: UpdateFunction, renderFn: RenderFunction) => {
  const { canvasRef, reset } = useAnimationLoop(updateFn, renderFn);
  const { setIsPlaying } = useFrameManagement();

  useCanvasResize(canvasRef);

  const startAnimation = () => setIsPlaying(true);
  const stopAnimation = () => setIsPlaying(false);

  return { canvasRef, startAnimation, stopAnimation, reset };
};