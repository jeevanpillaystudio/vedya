import { create } from 'zustand';

interface FrameState {
  currentFrame: number;
  totalFrames: number;
  isPlaying: boolean;
  setCurrentFrame: (frame: number) => void;
  setTotalFrames: (frames: number) => void;
  setIsPlaying: (isPlaying: boolean) => void;
  incrementFrame: () => void;
  resetFrame: () => void;
}

export const useFrameStore = create<FrameState>((set) => ({
  currentFrame: 0,
  totalFrames: 0,
  isPlaying: false,
  setCurrentFrame: (frame) => set({ currentFrame: frame }),
  setTotalFrames: (frames) => set({ totalFrames: frames }),
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  incrementFrame: () => set((state) => ({ 
    currentFrame: Math.min(state.currentFrame + 1, state.totalFrames - 1) 
  })),
  resetFrame: () => set({ currentFrame: 0 }),
}));
