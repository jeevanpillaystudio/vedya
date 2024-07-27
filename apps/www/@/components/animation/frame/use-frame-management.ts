import { useCallback, useEffect, useRef } from 'react';
import { useFrameStore } from './frame-store';
import { useControlStore } from '../control/control-store';
import { FIXED_TIME_STEP } from '../default';

export const useFrameManagement = () => {
  const { 
    currentFrame, 
    totalFrames, 
    isPlaying, 
    setCurrentFrame, 
    setTotalFrames, 
    setIsPlaying, 
    incrementFrame, 
    resetFrame 
  } = useFrameStore();
  const { duration } = useControlStore();
  const frameIntervalRef = useRef<number | null>(null);

  const calculateTotalFrames = useCallback(() => {
    const frames = Math.ceil(duration / FIXED_TIME_STEP);
    setTotalFrames(frames);
  }, [duration, setTotalFrames]);

  const startFrameLoop = useCallback(() => {
    if (frameIntervalRef.current === null) {
      frameIntervalRef.current = window.setInterval(() => {
        incrementFrame();
      }, FIXED_TIME_STEP);
    }
  }, [incrementFrame]);

  const stopFrameLoop = useCallback(() => {
    if (frameIntervalRef.current !== null) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    calculateTotalFrames();
  }, [duration, calculateTotalFrames]);

  useEffect(() => {
    if (isPlaying) {
      startFrameLoop();
    } else {
      stopFrameLoop();
    }
    return () => stopFrameLoop();
  }, [isPlaying, startFrameLoop, stopFrameLoop]);

  return {
    currentFrame,
    totalFrames,
    isPlaying,
    setCurrentFrame,
    setIsPlaying,
    resetFrame,
  };
};