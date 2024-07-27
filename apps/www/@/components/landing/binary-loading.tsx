import React, { useCallback, useMemo, useEffect } from "react";
import { cn } from "@/lib/utils";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";
import { useAnimationStore } from "../animation/animation-store";
import { type CanvasSize } from "../animation/types";
import { useCanvasAnimation } from "../animation/hooks/use-canvas-animation";

const BinaryLoading: React.FC = () => {
  const { duration, restart } = useAnimationStore();

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

  const { canvasRef, reset } = useCanvasAnimation(updateFn, renderFn);

  const canvasStyle = useMemo(() => ({ height: "100%", width: "100%" }), []);

  useEffect(() => {
    reset();
  }, [restart, reset]);

  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-black")}>
      <canvas ref={canvasRef} style={canvasStyle} />
    </div>
  );
};

export default React.memo(BinaryLoading);
