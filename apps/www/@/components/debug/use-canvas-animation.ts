import { useRef, useCallback, useEffect } from 'react';
import { useDebugAnimationStore } from './debug-animation-store';

export interface CanvasSize {
  width: number;
  height: number;
}

type UpdateFunction = (deltaTime: number, elapsedTime: number) => void;
type RenderFunction = (ctx: CanvasRenderingContext2D, size: CanvasSize, elapsedTime: number) => void;

export const useCanvasAnimation = (
  updateFn: UpdateFunction,
  renderFn: RenderFunction
) => {
  const {
    duration,
    debug,
    isPlaying,
    setDebugInfo,
    setOnNextFrame,
    handleRestart
  } = useDebugAnimationStore();

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const frameCountRef = useRef(0);
  const maxDuration = 5000; // 5 seconds in milliseconds

  const gameLoop = useCallback((currentTime: number) => {
    if (!startTimeRef.current) startTimeRef.current = currentTime;
    const elapsedTime = currentTime - startTimeRef.current;
    const deltaTime = currentTime - lastFrameTimeRef.current;
    lastFrameTimeRef.current = currentTime;

    updateFn(deltaTime / 1000, elapsedTime / 1000);

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (canvas && ctx) {
      const size: CanvasSize = { width: canvas.width, height: canvas.height };
      renderFn(ctx, size, elapsedTime / 1000);
    }

    frameCountRef.current++;
    setDebugInfo({
      progress: Math.min(elapsedTime / duration, 1),
      frameCount: frameCountRef.current,
      fps: Math.round(1000 / deltaTime)
    });

    if (elapsedTime < duration && elapsedTime < maxDuration) {
      animationRef.current = requestAnimationFrame(gameLoop);
    } else {
      stopAnimation();
    }
  }, [duration, updateFn, renderFn, setDebugInfo]);

  const startAnimation = useCallback(() => {
    startTimeRef.current = 0;
    lastFrameTimeRef.current = 0;
    frameCountRef.current = 0;
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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const resizeCanvas = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
      };

      resizeCanvas();
      window.addEventListener("resize", resizeCanvas);

      return () => {
        window.removeEventListener("resize", resizeCanvas);
        stopAnimation();
      };
    }
  }, [stopAnimation]);

  useEffect(() => {
    if (isPlaying) {
      startAnimation();
    } else {
      stopAnimation();
    }
  }, [isPlaying, startAnimation, stopAnimation]);

  useEffect(() => {
    setOnNextFrame(() => {
      if (animationRef.current === null) {
        requestAnimationFrame(gameLoop);
      }
    });
  }, [gameLoop, setOnNextFrame]);

  useEffect(() => {
    handleRestart();
  }, [handleRestart]);

  return { canvasRef };
};