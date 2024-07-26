import React, { useEffect } from "react";
import { useCanvasAnimation } from "@/lib/hooks/use-canvas-animation";
import { cn } from "@/lib/utils";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";
import { useDebugAnimationStore } from "../debug/debug-animation-store";

const BinaryLoading: React.FC = () => {
  const { duration, debug, isPlaying, restart, setOnNextFrame, setDebugInfo } = useDebugAnimationStore();

  const { canvasRef, debugInfo, handleNextFrame, startAnimation, stopAnimation } = useCanvasAnimation(
    (ctx, size, progress, deltaTime) => {
      const { currentSize } = drawBinaryGrid(ctx, size, progress, deltaTime);
      // setDebugInfo({ progress, currentSize, frameCount: debugInfo.frameCount + 1 });
    },
    { duration, debug, isPlaying },
  );

  useEffect(() => {
    if (isPlaying) {
      startAnimation();
    } else {
      stopAnimation();
    }
  }, [isPlaying, startAnimation, stopAnimation]);

  useEffect(() => {
    if (restart) {
      startAnimation();
    }
  }, [restart, startAnimation]);

  // useEffect(() => {
  //   setOnNextFrame(handleNextFrame);
  // }, [handleNextFrame, setOnNextFrame]);

  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-black")}>
      <canvas ref={canvasRef} className="h-full w-full border" />
    </div>
  );
};

export default BinaryLoading;
