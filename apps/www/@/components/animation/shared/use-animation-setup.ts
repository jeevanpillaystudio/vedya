import { useCallback } from "react";
import { useFrameManagement } from "../frame/use-frame-management";
import { type CanvasSize } from "../types";
import { useControlStore } from "../control/control-store";
import { useCanvasAnimation } from "./use-canvas-animation";

export interface AnimationSetupInterface {
    drawFn: (ctx: CanvasRenderingContext2D, size: CanvasSize, currentFrame: number) => void;
}

export const useAnimationSetup = ({ drawFn }: AnimationSetupInterface) => {
  const { duration } = useControlStore();
  const { totalFrames } = useFrameManagement();

  const updateFn = useCallback((deltaTime: number, currentFrame: number) => {
    // Update game state here if needed
  }, []);

  const renderFn = useCallback(
    (ctx: CanvasRenderingContext2D, size: CanvasSize, currentFrame: number) => {
      const progress = Math.min(currentFrame / (totalFrames - 1), 1);
      drawFn(ctx, size, currentFrame);
    },
    [drawFn, totalFrames],
  );

  const { canvasRef, reset } = useCanvasAnimation(updateFn, renderFn);

  return { canvasRef, reset };
};