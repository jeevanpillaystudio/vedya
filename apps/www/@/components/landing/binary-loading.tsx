import React, { useCallback } from "react";
import { cn } from "@/lib/utils";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";
import { useDebugAnimationStore } from "../debug/debug-animation-store";
import { type CanvasSize } from "../debug/types";
import { useCanvasAnimation } from "../debug";

const BinaryLoading: React.FC = () => {
  const { duration } = useDebugAnimationStore();

  const updateFn = useCallback((deltaTime: number, elapsedTime: number) => {
    // Update game state here if needed
  }, []);

  const renderFn = useCallback(
    (ctx: CanvasRenderingContext2D, size: CanvasSize, elapsedTime: number) => {
      const progress = Math.min(elapsedTime / (duration / 1000), 1);
      drawBinaryGrid(ctx, size, progress);
    },
    [duration],
  );

  const { canvasRef } = useCanvasAnimation(updateFn, renderFn);

  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-black")}>
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  );
};

export default BinaryLoading;
