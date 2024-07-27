import { useCallback } from 'react';
import { useFrameStore } from '../frame/frame-store';
import { useControlStore } from './control-store';

export const useRestart = () => {
  const { handleRestart } = useControlStore();
  const { resetFrame } = useFrameStore();

  const restart = useCallback(() => {
    handleRestart();
    resetFrame();
  }, [handleRestart, resetFrame]);

  return { restart };
};