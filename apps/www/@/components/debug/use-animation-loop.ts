import { useCallback, useRef } from 'react';
import { useDebugAnimationStore } from './debug-animation-store';
import { type UpdateFunction, type RenderFunction, type AnimationState, type CanvasSize } from './types';

export const useAnimationLoop = (updateFn: UpdateFunction, renderFn: RenderFunction) => {
  const { duration, setDebugInfo } = useDebugAnimationStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const stateRef = useRef<AnimationState>({ startTime: 0, lastFrameTime: 0, frameCount: 0 });
  const maxDuration = 5000; // 5 seconds in milliseconds

  const gameLoop = useCallback((currentTime: number) => {
    const state = stateRef.current;
    if (!state.startTime) state.startTime = currentTime;
    const elapsedTime = currentTime - state.startTime;
    const deltaTime = currentTime - state.lastFrameTime;
    state.lastFrameTime = currentTime;

    updateFn(deltaTime / 1000, elapsedTime / 1000);

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (canvas && ctx) {
      const size: CanvasSize = { width: canvas.width, height: canvas.height };
      renderFn(ctx, size, elapsedTime / 1000);
    }

    state.frameCount++;
    setDebugInfo({
      progress: Math.min(elapsedTime / duration, 1),
      frameCount: state.frameCount,
      fps: Math.round(1000 / deltaTime)
    });

    if (elapsedTime < duration && elapsedTime < maxDuration) {
      animationRef.current = requestAnimationFrame(gameLoop);
    } else {
      // Stop animation logic here
    }
  }, [duration, updateFn, renderFn, setDebugInfo]);

  return { canvasRef, animationRef, stateRef, gameLoop };
};
