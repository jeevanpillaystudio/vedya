import { useCallback, useEffect } from 'react';
import { useAnimationStore } from '../animation-store';
import { type AnimationState } from '../types';

export const useAnimationControls = (
  animationRef: React.MutableRefObject<number | null>,
  stateRef: React.MutableRefObject<AnimationState>,
  gameLoop: (currentTime: number) => void
) => {
  const { isPlaying, setOnNextFrame, handleRestart } = useAnimationStore();

  const startAnimation = useCallback(() => {
    stateRef.current = { startTime: 0, lastFrameTime: 0, frameCount: 0 };
    if (animationRef.current === null) {
      animationRef.current = requestAnimationFrame(gameLoop);
    }
  }, [animationRef, stateRef, gameLoop]);

  const stopAnimation = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, [animationRef]);

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
  }, [gameLoop, setOnNextFrame, animationRef]);

  useEffect(() => {
    handleRestart();
  }, [handleRestart]);

  return { startAnimation, stopAnimation };
};
