import { useCallback } from "react";
import { useAnimationStore } from "../animation-store";
import { useCanvasAnimation } from "./use-canvas-animation";
import { type CanvasSize } from "../types";

export interface AnimationSetupInterface {
    drawFn: (ctx: CanvasRenderingContext2D, size: CanvasSize, elapsedTime: number) => void;
}

export const useAnimationSetup = ({ drawFn }: AnimationSetupInterface) => {
  const { duration } = useAnimationStore();

  const updateFn = useCallback((deltaTime: number, elapsedTime: number) => {
    // Update game state hereif needed
  }, []);

  const renderFn = useCallback(
    (ctx: CanvasRenderingContext2D, size: CanvasSize, elapsedTime: number) => {
      const progress = Math.min(elapsedTime / (duration / 1000), 1);
      drawFn(ctx, size, progress);
    },
    [drawFn, duration],
  );

  const { canvasRef, reset } = useCanvasAnimation(updateFn, renderFn);

  return { canvasRef, reset };
};
