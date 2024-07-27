import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAnimationStore } from "./animation-store";
import { PlayIcon, PauseIcon, SkipForwardIcon, RefreshCwIcon, StopCircleIcon } from "lucide-react";
import { Slider } from "../ui/slider";
import { MAX_DURATION } from "./default";

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
    <Card className="fixed left-1/2 top-2 z-10 -translate-x-1/2 transform text-foreground">
      <CardContent className="p-2">
        <div className="mb-2 flex items-center space-x-2">
          <Button size="icon" variant="outline" onClick={handlePlayPauseClick}>
            {isPlaying ? <PauseIcon size={12} /> : <PlayIcon size={12} />}
          </Button>
          <Button size="icon" variant="outline" onClick={handleStopClick} disabled={!isPlaying && !isPaused}>
            <StopCircleIcon size={16} />
          </Button>
          <Button size="icon" variant="outline" onClick={continueOneFrame} disabled={isPlaying}>
            <SkipForwardIcon size={16} />
          </Button>
          <Button size="icon" variant="outline" onClick={handleRestart}>
            <RefreshCwIcon size={16} />
          </Button>
          <div className="text-xs">
            <p>Progress: {debugInfo.progress.toFixed(2)}</p>
            <p>Size: {debugInfo.currentSize}</p>
            <p>Frames: {debugInfo.frameCount}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Slider
            // className="w-32"
            min={1000}
            max={MAX_DURATION}
            step={100}
            value={[duration]}
            onValueChange={(value) => setDuration(value[0]!)}
          />
          <span className="text-xs">{duration}ms</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(AnimationControlPanel);
