import { useCallback, useEffect, useRef } from 'react';
import { useAnimationStore } from '../animation-store';
import { type AnimationState } from '../types';

export const useAnimationControls = (
  animationRef: React.MutableRefObject<number | null>,
  stateRef: React.MutableRefObject<AnimationState>,
  gameLoop: (currentTime: number) => void
) => {
  const { isPlaying, isPaused, restart } = useAnimationStore();
  const isFirstRender = useRef(true);

  const startAnimation = useCallback(() => {
    if (animationRef.current === null) {
      animationRef.current = requestAnimationFrame(gameLoop);
    }
  }, [animationRef, gameLoop]);

  const stopAnimation = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, [animationRef]);

  const resetAnimation = useCallback(() => {
    stopAnimation();
    stateRef.current = { startTime: 0, lastFrameTime: 0, frameCount: 0, accumulatedTime: 0 };
  }, [stopAnimation, stateRef]);

  useEffect(() => {
    if (isPlaying && !isPaused) {
      startAnimation();
    } else {
      stopAnimation();
    }
  }, [isPlaying, isPaused, startAnimation, stopAnimation]);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
    } else {
      resetAnimation();
    }
  }, [restart, resetAnimation]);

  return { startAnimation, stopAnimation, resetAnimation };
};