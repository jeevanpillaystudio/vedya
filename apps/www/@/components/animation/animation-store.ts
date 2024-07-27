import { create } from 'zustand';

interface AnimationState {
  isPlaying: boolean;
  debug: boolean;
  duration: number;
  restart: number;
  debugInfo: {
    progress: number;
    currentSize?: number; // @todo double check
    frameCount: number;
    fps: number;
  }
  onNextFrame: () => void;
  setIsPlaying: (isPlaying: boolean) => void;
  setDebug: (debug: boolean) => void;
  setDuration: (duration: number) => void;
  handleRestart: () => void;
  setDebugInfo: (debugInfo: Partial<AnimationState['debugInfo']>) => void;
  setOnNextFrame: (callback: () => void) => void;
}

// @todo make defaults
export const useAnimationStore = create<AnimationState>((set) => ({
  isPlaying: false,
  debug: false,
  duration: 5000,
  restart: 0,
  debugInfo: { progress: 0, currentSize: 0, frameCount: 0, fps: 24 },
  onNextFrame: () => {},
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setDebug: (debug) => set({ debug }),
  setDuration: (duration) => set({ duration }),
  handleRestart: () => set((state) => ({ restart: state.restart + 1, isPlaying: true })),
  setDebugInfo: (debugInfo) => set((state) => ({ debugInfo: { ...state.debugInfo, ...debugInfo } })),
  setOnNextFrame: (callback) => set({ onNextFrame: callback }),
}));