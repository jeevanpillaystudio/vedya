import { create } from 'zustand';
import { MAX_DURATION } from './default';

interface AnimationState {
  isPlaying: boolean;
  isPaused: boolean;
  isCompleted: boolean;
  duration: number;
  restart: number;
  debugInfo: {
    progress: number;
    currentSize?: number;
    frameCount: number;
  };
  setIsPlaying: (isPlaying: boolean) => void;
  setIsPaused: (isPaused: boolean) => void;
  setIsCompleted: (isCompleted: boolean) => void;
  setDuration: (duration: number) => void;
  handleRestart: () => void;
  setDebugInfo: (debugInfo: Partial<AnimationState['debugInfo']>) => void;
  continueOneFrame: () => void;
}

export const useAnimationStore = create<AnimationState>((set, get) => ({
  isPlaying: false,
  isPaused: false,
  isCompleted: false,
  duration: 5000,
  restart: 0,
  debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  setIsPlaying: (isPlaying) => set({ isPlaying, isPaused: false }),
  setIsPaused: (isPaused) => set({ isPaused, isPlaying: false }),
  setIsCompleted: (isCompleted) => set({ isCompleted, isPlaying: false, isPaused: false }),
  setDuration: (duration) => set({ duration: Math.min(duration, MAX_DURATION) }),
  handleRestart: () => set((state) => ({ 
    restart: state.restart + 1, 
    isPlaying: false, 
    isPaused: false,
    isCompleted: false,
    debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  })),
  setDebugInfo: (debugInfo) => set((state) => ({ 
    debugInfo: { ...state.debugInfo, ...debugInfo },
    isCompleted: debugInfo.progress !== undefined && debugInfo.progress >= 1,
  })),
  continueOneFrame: () => {
    const { isPlaying, isPaused, isCompleted } = get();
    if (!isPlaying && !isPaused && !isCompleted) {
      set({ isPlaying: true });
      setTimeout(() => set({ isPlaying: false }), 0);
    }
  },
}));