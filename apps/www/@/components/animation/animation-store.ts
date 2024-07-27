import { create } from 'zustand';

interface AnimationState {
  isPlaying: boolean;
  debug: boolean;
  duration: number;
  restart: number;
  debugInfo: {
    progress: number;
    currentSize?: number;
    frameCount: number;
  };
  onNextFrame: (() => void) | null;
  setIsPlaying: (isPlaying: boolean) => void;
  setDebug: (debug: boolean) => void;
  setDuration: (duration: number) => void;
  handleRestart: () => void;
  setDebugInfo: (debugInfo: Partial<AnimationState['debugInfo']>) => void;
  setOnNextFrame: (callback: (() => void) | null) => void;
  triggerNextFrame: () => void;
}

export const useAnimationStore = create<AnimationState>((set, get) => ({
  isPlaying: false,
  debug: false,
  duration: 5000,
  restart: 0,
  debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  onNextFrame: null,
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setDebug: (debug) => set({ debug }),
  setDuration: (duration) => set({ duration }),
  handleRestart: () => set((state) => ({ restart: state.restart + 1, isPlaying: true })),
  setDebugInfo: (debugInfo) => set((state) => ({ debugInfo: { ...state.debugInfo, ...debugInfo } })),
  setOnNextFrame: (callback) => set({ onNextFrame: callback }),
  triggerNextFrame: () => {
    const { onNextFrame } = get();
    if (onNextFrame) {
      onNextFrame();
    }
  },
}));