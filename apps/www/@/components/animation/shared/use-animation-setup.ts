import { useCallback } from "react";
import { type CanvasSize } from "../types";
import { useCanvasAnimation } from "./use-canvas-animation";

export interface AnimationSetupInterface {
    drawFn: (ctx: CanvasRenderingContext2D, size: CanvasSize, currentFrame: number) => void;
}

export const useAnimationSetup = ({ drawFn }: AnimationSetupInterface) => {
  const updateFn = useCallback((deltaTime: number, currentFrame: number) => {
    // Update game state here if needed
  }, []);

  const renderFn = useCallback(
    (ctx: CanvasRenderingContext2D, size: CanvasSize, currentFrame: number) => {
      drawFn(ctx, size, currentFrame);
    },
    [drawFn],
  );

  const { canvasRef, reset } = useCanvasAnimation(updateFn, renderFn);

  return { canvasRef, reset };
};