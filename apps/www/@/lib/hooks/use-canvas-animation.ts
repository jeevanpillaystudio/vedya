import { useRef, useState, useEffect, useCallback } from 'react';

export interface CanvasSize {
  width: number;
  height: number;
}

export interface AnimationProps {
  duration: number;
  debug: boolean;
  isPlaying: boolean;
}

export interface DebugInfo {
  progress: number;
  frameCount: number;
  currentSize?: number;
  [key: string]: any;
}

type DrawFunction = (
  ctx: CanvasRenderingContext2D,
  size: CanvasSize,
  progress: number,
  deltaTime: number
) => void;

export const useCanvasAnimation = (
  drawFn: DrawFunction,
  { duration, debug, isPlaying }: AnimationProps
) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo>({ progress: 0, frameCount: 0 });
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef(Date.now());
  const lastFrameTimeRef = useRef(Date.now());
  const maxDuration = 5000; // 5 seconds in milliseconds

  const updateCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const currentTime = Date.now();
    const elapsedTime = currentTime - startTimeRef.current;
    const deltaTime = currentTime - lastFrameTimeRef.current;
    lastFrameTimeRef.current = currentTime;

    const progress = Math.min(elapsedTime / duration, 1);
    const size: CanvasSize = { width: canvas.width, height: canvas.height };

    drawFn(ctx, size, progress, deltaTime);

    setDebugInfo((prev) => ({ 
      ...prev,
      progress, 
      frameCount: prev.frameCount + 1 
    }));

    if (progress < 1 && elapsedTime < maxDuration) {
      animationRef.current = requestAnimationFrame(updateCanvas);
    } else {
      stopAnimation();
    }
  }, [duration, drawFn]);

  const startAnimation = useCallback(() => {
    startTimeRef.current = Date.now();
    lastFrameTimeRef.current = Date.now();
    setDebugInfo((prev) => ({ ...prev, frameCount: 0 }));
    if (animationRef.current === null) {
      animationRef.current = requestAnimationFrame(updateCanvas);
    }
  }, [updateCanvas]);

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
        updateCanvas();
      };

      resizeCanvas();
      window.addEventListener("resize", resizeCanvas);

      return () => {
        window.removeEventListener("resize", resizeCanvas);
        stopAnimation();
      };
    }
  }, [updateCanvas, stopAnimation]);

  const handleNextFrame = () => {
    updateCanvas();
  };

  return { canvasRef, debugInfo, handleNextFrame, setDebugInfo, startAnimation, stopAnimation };
};