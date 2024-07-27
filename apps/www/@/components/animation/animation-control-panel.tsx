import React, { useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnimationStore } from "./animation-store";

const PlayButton = React.memo(({ isPlaying, onClick }: { isPlaying: boolean; onClick: () => void }) => (
  <Button variant={isPlaying ? "destructive" : "default"} onClick={onClick}>
    {isPlaying ? "Stop" : "Play"}
  </Button>
));

PlayButton.displayName = "PlayButton";

const RestartButton = React.memo(({ onClick }: { onClick: () => void }) => <Button onClick={onClick}>Restart</Button>);

RestartButton.displayName = "RestartButton";

const DebugSwitch = React.memo(({ debug, setDebug }: { debug: boolean; setDebug: (debug: boolean) => void }) => (
  <div className="flex items-center space-x-2">
    <Switch id="debug-mode" checked={debug} onCheckedChange={setDebug} />
    <label htmlFor="debug-mode" className="text-white">
      Debug Mode
    </label>
  </div>
));

DebugSwitch.displayName = "DebugSwitch";

const AnimationControlPanel: React.FC = () => {
  const { isPlaying, setIsPlaying, debug, setDebug, duration, setDuration, handleRestart, debugInfo, triggerNextFrame } =
    useAnimationStore();

  const handlePlayClick = useCallback(() => setIsPlaying(!isPlaying), [isPlaying, setIsPlaying]);
  const handleDurationChange = useCallback((value: number[]) => setDuration(value[0]!), [setDuration]);

  const debugInfoMemo = useMemo(
    () => (
      <>
        Progress: {debugInfo.progress.toFixed(2)}
        <br />
        Current Size: {debugInfo.currentSize}
        <br />
        Frame Count: {debugInfo.frameCount}
      </>
    ),
    [debugInfo.progress, debugInfo.currentSize, debugInfo.frameCount],
  );

  return (
    <Card className="fixed right-4 top-4 z-10 w-64 bg-black/50 text-white">
      <CardHeader>
        <CardTitle>Animation Control</CardTitle>
        <CardDescription className="text-gray-300">Adjust animation settings</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between">
          <PlayButton isPlaying={isPlaying} onClick={handlePlayClick} />
          <RestartButton onClick={handleRestart} />
        </div>
        <DebugSwitch debug={debug} setDebug={setDebug} />
        <div>
          <label htmlFor="duration" className="block text-sm font-medium">
            Duration: {duration}ms
          </label>
          <Slider id="duration" min={1000} max={10000} step={100} value={[duration]} onValueChange={handleDurationChange} />
        </div>
        {debug && (
          <>
            <Button onClick={triggerNextFrame}>Next Frame</Button>
            <div className="mt-2">{debugInfoMemo}</div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default React.memo(AnimationControlPanel);
