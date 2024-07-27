import { useCallback } from 'react';
import { useFrameStore } from '../frame/frame-store';
import { useControlStore } from './control-store';

export const usePlayPause = () => {
  const { setIsPlaying, setIsPaused } = useControlStore();
  const { isPlaying, setIsPlaying: setFrameIsPlaying } = useFrameStore();

  const togglePlayPause = useCallback(() => {
    if (isPlaying) {
      setIsPaused(true);
      setFrameIsPlaying(false);
    } else {
      setIsPlaying(true);
      setIsPaused(false);
      setFrameIsPlaying(true);
    }
  }, [isPlaying, setIsPlaying, setIsPaused, setFrameIsPlaying]);

  return { togglePlayPause };
};