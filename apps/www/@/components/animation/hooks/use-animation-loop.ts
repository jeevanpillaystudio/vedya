import { useCallback, useRef, useEffect } from 'react';
import { type UpdateFunction, type RenderFunction, type CanvasSize, type AnimationState } from '../types';
import { useAnimationStore } from '../animation-store';
import { FIXED_TIME_STEP, MAX_DURATION } from '../default';

export const useAnimationLoop = (updateFn: UpdateFunction, renderFn: RenderFunction) => {
  const { duration, setDebugInfo, restart } = useAnimationStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const stateRef = useRef<AnimationState>({
    startTime: 0,
    lastFrameTime: 0,
    frameCount: 0,
    accumulatedTime: 0,
  });

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, []);

  const gameLoop = useCallback((currentTime: number) => {
    const state = stateRef.current;
    if (!state.startTime) state.startTime = currentTime;
    const elapsedTime = currentTime - state.startTime;
    const deltaTime = currentTime - state.lastFrameTime;
    state.lastFrameTime = currentTime;

    state.accumulatedTime += deltaTime;

    while (state.accumulatedTime >= FIXED_TIME_STEP) {
      updateFn(FIXED_TIME_STEP / 1000, elapsedTime / 1000);
      state.accumulatedTime -= FIXED_TIME_STEP;
    }

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
    });

    if (elapsedTime < duration && elapsedTime < MAX_DURATION) {
      animationRef.current = requestAnimationFrame(gameLoop);
    } else {
      // Stop animation logic here
    }
  }, [duration, updateFn, renderFn, setDebugInfo]);

  const startAnimation = useCallback(() => {
    stateRef.current = { startTime: 0, lastFrameTime: 0, frameCount: 0, accumulatedTime: 0 };
    if (animationRef.current === null) {
      animationRef.current = requestAnimationFrame(gameLoop);
    }
  }, [gameLoop]);

  const stopAnimation = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    clearCanvas();
    stateRef.current = { startTime: 0, lastFrameTime: 0, frameCount: 0, accumulatedTime: 0 };
    setDebugInfo({ progress: 0, currentSize: 0, frameCount: 0 });
  }, [clearCanvas, setDebugInfo]);

  useEffect(() => {
    reset();
  }, [restart, reset]);

  return { canvasRef, animationRef, stateRef, gameLoop, startAnimation, stopAnimation, reset };
};