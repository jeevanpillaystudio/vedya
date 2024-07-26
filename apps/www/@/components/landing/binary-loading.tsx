import React, { useEffect } from "react";
import { useCanvasAnimation } from "@/lib/hooks/use-canvas-animation";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";
import { cn } from "@/lib/utils";

interface BinaryLoadingProps {
  duration: number;
  debug: boolean;
  isPlaying: boolean;
  restart: number;
  onNextFrame: () => void;
}

const BinaryLoading: React.FC<BinaryLoadingProps> = ({ duration, debug, isPlaying, restart, onNextFrame }) => {
  const { canvasRef, debugInfo, handleNextFrame, setDebugInfo, startAnimation, stopAnimation } = useCanvasAnimation(
    (ctx, size, progress, deltaTime) => {
      const { currentSize } = drawBinaryGrid(ctx, size, progress, deltaTime);
      setDebugInfo((prev) => ({ ...prev, currentSize }));
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

  useEffect(() => {
    if (debug) {
      onNextFrame = handleNextFrame;
    }
  }, [debug, handleNextFrame, onNextFrame]);

  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-black")}>
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  );
};

export default BinaryLoading;
