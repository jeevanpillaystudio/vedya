import React from "react";
import { cn } from "../../_react/css-utils";

interface AnimationControlProps {
  isPlaying: boolean;
  setIsPlaying: (isPlaying: boolean) => void;
  debug: boolean;
  setDebug: (debug: boolean) => void;
  duration: number;
  setDuration: (duration: number) => void;
  onRestart: () => void;
}

const AnimationControl: React.FC<AnimationControlProps> = ({
  isPlaying,
  setIsPlaying,
  debug,
  setDebug,
  duration,
  setDuration,
  onRestart,
}) => {
  return (
    <div className="absolute right-4 top-4 flex flex-col items-end space-y-2 rounded bg-gray-800 p-4 text-white">
      <div className="flex space-x-2">
        <button
          className={cn("rounded px-4 py-2 font-bold", isPlaying ? "bg-red-500 hover:bg-red-700" : "bg-green-500 hover:bg-green-700")}
          onClick={() => setIsPlaying(!isPlaying)}
        >
          {isPlaying ? "Stop" : "Play"}
        </button>
        <button className="rounded bg-blue-500 px-4 py-2 font-bold hover:bg-blue-700" onClick={onRestart}>
          Restart
        </button>
      </div>
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="debug"
          checked={debug}
          onChange={(e) => setDebug(e.target.checked)}
          className="form-checkbox h-5 w-5 text-blue-600"
        />
        <label htmlFor="debug">Debug Mode</label>
      </div>
      <div className="flex items-center space-x-2">
        <label htmlFor="speed">Speed:</label>
        <input
          type="range"
          id="speed"
          min="1000"
          max="10000"
          step="1000"
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          className="form-range h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
        />
        <span>{duration / 1000}s</span>
      </div>
    </div>
  );
};

export default AnimationControl;
