import { useCallback } from 'react';
import { useFrameStore } from '../frame/frame-store';

export const useContinueFrame = () => {
  const { incrementFrame } = useFrameStore();

  const continueOneFrame = useCallback(() => {
    incrementFrame();
  }, [incrementFrame]);

  return { continueOneFrame };
};