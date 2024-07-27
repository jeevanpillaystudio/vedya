import React from "react";
import { PlayIcon, PauseIcon, SkipForwardIcon, RefreshCwIcon } from "lucide-react";
import { useFrameManagement } from "./frame/use-frame-management";
import { usePlayPause } from "./control/use-play-pause";
import { useContinueFrame } from "./control/use-continue-frame";
import { useRestart } from "./control/use-restart";
import { useControlStore } from "./control/control-store";
import { useDebugStore } from "./debug/debug-store";
import { MAX_DURATION } from "./default";
import { Card, CardContent } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";

const Animation: React.FC = () => {
  const { togglePlayPause } = usePlayPause();
  const { continueOneFrame } = useContinueFrame();
  const { restart } = useRestart();
  const { currentFrame, totalFrames, isPlaying } = useFrameManagement();
  const { duration, setDuration } = useControlStore();
  const { debugInfo } = useDebugStore();

  return (
    <Card className="fixed left-1/2 top-2 z-10 -translate-x-1/2 transform text-foreground">
      <CardContent className="p-2">
        <div className="mb-2 flex items-center space-x-2">
          <Button size="icon" variant="outline" onClick={togglePlayPause}>
            {isPlaying ? <PauseIcon size={12} /> : <PlayIcon size={12} />}
          </Button>
          <Button size="icon" variant="outline" onClick={continueOneFrame} disabled={isPlaying}>
            <SkipForwardIcon size={16} />
          </Button>
          <Button size="icon" variant="outline" onClick={restart}>
            <RefreshCwIcon size={16} />
          </Button>
          <div className="text-xs">
            <p>
              Frame: {currentFrame + 1} / {totalFrames}
            </p>
            <p>Progress: {debugInfo.progress.toFixed(2)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Slider min={1000} max={MAX_DURATION} step={100} value={[duration]} onValueChange={(value) => setDuration(value[0]!)} />
          <span className="text-xs">{duration}ms</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(Animation);
