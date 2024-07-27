import { useCallback, useEffect } from 'react';
import { useAnimationStore } from '../animation-store';
import { type AnimationState } from '../types';

export const useAnimationControls = (
  animationRef: React.MutableRefObject<number | null>,
  stateRef: React.MutableRefObject<AnimationState>,
  gameLoop: (currentTime: number) => void
) => {
  const { isPlaying, isPaused } = useAnimationStore();

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

  useEffect(() => {
    if (isPlaying && !isPaused) {
      startAnimation();
    } else {
      stopAnimation();
    }
  }, [isPlaying, isPaused, startAnimation, stopAnimation]);

  return { startAnimation, stopAnimation };
};