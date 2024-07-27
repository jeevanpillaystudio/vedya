import { create } from 'zustand';

interface DebugState {
  debugInfo: {
    progress: number;
    currentSize?: number;
    frameCount: number;
  };
  setDebugInfo: (debugInfo: Partial<DebugState['debugInfo']>) => void;
}

export const useDebugStore = create<DebugState>((set) => ({
  debugInfo: { progress: 0, currentSize: 0, frameCount: 0 },
  setDebugInfo: (debugInfo) => set((state) => ({ 
    debugInfo: { ...state.debugInfo, ...debugInfo },
  })),
}));