import { create } from 'zustand';
import { MAX_DURATION } from './default';

interface AnimationState {
  isPlaying: boolean;
  isPaused: boolean;
  duration: number;
  restart: number;
  debugInfo: {
    progress: number;
    currentSize?: number;
    frameCount: number;
  };
  setIsPlaying: (isPlaying: boolean) => void;
  setIsPaused: (isPaused: boolean) => void;
  setDuration: (duration: number) => void;
  handleRestart: () => void;
  setDebugInfo: (debugInfo: Partial<AnimationState['debugInfo']>) => void;
  continueOneFrame: () => void;
}

export const useAnimationStore = create<AnimationState>((set, get) => ({
  isPlaying: false,
  isPaused: false,
  duration: 5000,
  restart: 0,
  debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  setIsPlaying: (isPlaying) => set({ isPlaying, isPaused: false }),
  setIsPaused: (isPaused) => set({ isPaused, isPlaying: false }),
  setDuration: (duration) => set({ duration: Math.min(duration, MAX_DURATION) }),
  handleRestart: () => set((state) => ({ 
    restart: state.restart + 1, 
    isPlaying: false, 
    isPaused: false,
    debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  })),
  setDebugInfo: (debugInfo) => set((state) => ({ debugInfo: { ...state.debugInfo, ...debugInfo } })),
  continueOneFrame: () => {
    const { isPlaying, isPaused } = get();
    if (!isPlaying && !isPaused) {
      set({ isPlaying: true });
      setTimeout(() => set({ isPlaying: false }), 0);
    }
  },
}));