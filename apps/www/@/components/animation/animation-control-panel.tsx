import React from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnimationStore } from "./animation-store";
import { PlayIcon, PauseIcon, SkipForwardIcon, RefreshCwIcon, StopCircleIcon } from "lucide-react";

const AnimationControlPanel: React.FC = () => {
  const { isPlaying, isPaused, setIsPlaying, setIsPaused, duration, setDuration, handleRestart, debugInfo, continueOneFrame } =
    useAnimationStore();

  const handlePlayPauseClick = () => {
    if (isPlaying) {
      setIsPaused(true);
    } else if (isPaused) {
      setIsPlaying(true);
    } else {
      setIsPlaying(true);
    }
  };

  const handleStopClick = () => {
    setIsPlaying(false);
    setIsPaused(false);
  };

  return (
    <Card className="fixed right-4 top-4 z-10 w-64 bg-black/50 text-white">
      <CardHeader>
        <CardTitle>Animation Control</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between">
          <Button onClick={handlePlayPauseClick}>{isPlaying ? <PauseIcon /> : <PlayIcon />}</Button>
          <Button onClick={handleStopClick} disabled={!isPlaying && !isPaused}>
            <StopCircleIcon />
          </Button>
          <Button onClick={continueOneFrame} disabled={isPlaying}>
            <SkipForwardIcon />
          </Button>
          <Button onClick={handleRestart}>
            <RefreshCwIcon />
          </Button>
        </div>
        <div>
          <label htmlFor="duration" className="block text-sm font-medium">
            Duration: {duration}ms
          </label>
          <Slider id="duration" min={1000} max={10000} step={100} value={[duration]} onValueChange={(value) => setDuration(value[0]!)} />
        </div>
        <div>
          <p>Progress: {debugInfo.progress.toFixed(2)}</p>
          <p>Current Size: {debugInfo.currentSize}</p>
          <p>Frame Count: {debugInfo.frameCount}</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(AnimationControlPanel);
