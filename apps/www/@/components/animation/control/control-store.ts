
import { create } from 'zustand';
import { MAX_DURATION } from '../default';

interface ControlState {
  isPlaying: boolean;
  isPaused: boolean;
  isCompleted: boolean;
  duration: number;
  restart: number;
  setIsPlaying: (isPlaying: boolean) => void;
  setIsPaused: (isPaused: boolean) => void;
  setIsCompleted: (isCompleted: boolean) => void;
  setDuration: (duration: number) => void;
  handleRestart: () => void;
  continueOneFrame: () => void;
}

export const useControlStore = create<ControlState>((set, get) => ({
  isPlaying: false,
  isPaused: false,
  isCompleted: false,
  duration: 5000,
  restart: 0,
  setIsPlaying: (isPlaying) => set({ isPlaying, isPaused: false }),
  setIsPaused: (isPaused) => set({ isPaused, isPlaying: false }),
  setIsCompleted: (isCompleted) => set({ isCompleted, isPlaying: false, isPaused: false }),
  setDuration: (duration) => set({ duration: Math.min(duration, MAX_DURATION) }),
  handleRestart: () => set((state) => ({ 
    restart: state.restart + 1, 
    isPlaying: false, 
    isPaused: false,
    isCompleted: false,
  })),
  continueOneFrame: () => {
    const { isPlaying, isPaused, isCompleted } = get();
    if (!isPlaying && !isPaused && !isCompleted) {
      set({ isPlaying: true });
      setTimeout(() => set({ isPlaying: false }), 0);
    }
  },
}));