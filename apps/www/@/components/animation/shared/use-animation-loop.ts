import { useCallback, useRef, useEffect } from 'react';
import { type UpdateFunction, type RenderFunction, type CanvasSize } from '../types';
import { useFrameManagement } from '../frame/use-frame-management';
import { useDebugStore } from '../debug/debug-store';
import { FIXED_TIME_STEP } from '../default';
  
export const useAnimationLoop = (updateFn: UpdateFunction, renderFn: RenderFunction) => {
  const { setDebugInfo } = useDebugStore();
  const { currentFrame, totalFrames} = useFrameManagement();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, []);

  const renderFrame = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (canvas && ctx) {
      const size: CanvasSize = { width: canvas.width, height: canvas.height };
      updateFn(FIXED_TIME_STEP / 1000, currentFrame);
      renderFn(ctx, size, currentFrame);
    }

    setDebugInfo({
      progress: Math.min(currentFrame / (totalFrames - 1), 1),
      frameCount: currentFrame,
    });
  }, [currentFrame, totalFrames, updateFn, renderFn, setDebugInfo]);

  useEffect(() => {
    renderFrame();
  }, [currentFrame, renderFrame]);

  const reset = useCallback(() => {
    clearCanvas();
    setDebugInfo({ progress: 0, currentSize: 0, frameCount: 0 });
  }, [clearCanvas, setDebugInfo]);

  return { canvasRef, reset };
};