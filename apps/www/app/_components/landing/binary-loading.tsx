import React from "react";
import { cn } from "../../_react/css-utils";
import { useCanvasAnimation } from "@/lib/hooks/use-canvas-animation";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";

interface BinaryLoadingProps {
  duration: number;
  debug: boolean;
  isPlaying: boolean;
  restart: number;
}

const BinaryLoading: React.FC<BinaryLoadingProps> = ({ duration, debug, isPlaying, restart }) => {
  const { canvasRef, debugInfo, handleNextFrame, setDebugInfo } = useCanvasAnimation(
    (ctx, size, progress, deltaTime) => {
      const { currentSize } = drawBinaryGrid(ctx, size, progress, deltaTime);
      setDebugInfo((prev) => ({ ...prev, currentSize }));
    },
    { duration, debug, isPlaying },
  );

  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-black")}>
      <canvas ref={canvasRef} className="h-full w-full" />
      {debug && (
        <div className="absolute bottom-4 left-4 text-white">
          <button className="rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700" onClick={handleNextFrame}>
            Next Frame
          </button>
          <div className="mt-2">
            Progress: {debugInfo.progress.toFixed(2)}
            <br />
            Current Size: {debugInfo.currentSize}
            <br />
            Frame Count: {debugInfo.frameCount}
          </div>
        </div>
      )}
    </div>
  );
};

export default BinaryLoading;
