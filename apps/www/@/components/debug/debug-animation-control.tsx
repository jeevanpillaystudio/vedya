import React from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDebugAnimationStore } from "./debug-animation-store";

const PlayButton: React.FC<{ isPlaying: boolean; onClick: () => void }> = ({ isPlaying, onClick }) => (
  <Button variant={isPlaying ? "destructive" : "default"} onClick={onClick}>
    {isPlaying ? "Stop" : "Play"}
  </Button>
);

const RestartButton: React.FC<{ onClick: () => void }> = ({ onClick }) => <Button onClick={onClick}>Restart</Button>;

const DebugSwitch: React.FC<{ debug: boolean; setDebug: (debug: boolean) => void }> = ({ debug, setDebug }) => (
  <div className="flex items-center space-x-2">
    <Switch id="debug-mode" checked={debug} onCheckedChange={setDebug} />
    <label htmlFor="debug-mode" className="text-white">
      Debug Mode
    </label>
  </div>
);

const DebugAnimationControl: React.FC = () => {
  const { isPlaying, setIsPlaying, debug, setDebug, duration, setDuration, handleRestart, debugInfo, onNextFrame } =
    useDebugAnimationStore();

  return (
    <div className="fixed right-4 top-4 z-10">
      <Card className="w-64 bg-black/50 text-white">
        <CardHeader>
          <CardTitle>Animation Control</CardTitle>
          <CardDescription className="text-gray-300">Adjust animation settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between">
            <PlayButton isPlaying={isPlaying} onClick={() => setIsPlaying(!isPlaying)} />
            <RestartButton onClick={handleRestart} />
          </div>
          <DebugSwitch debug={debug} setDebug={setDebug} />
          <div>
            <label htmlFor="duration" className="block text-sm font-medium">
              Duration: {duration}ms
            </label>
            <Slider id="duration" min={1000} max={10000} step={100} value={[duration]} onValueChange={(value) => setDuration(value[0]!)} />
          </div>
          {debug && (
            <>
              <Button onClick={onNextFrame}>Next Frame</Button>
              <div className="mt-2">
                Progress: {debugInfo.progress.toFixed(2)}
                <br />
                Current Size: {debugInfo.currentSize}
                <br />
                Frame Count: {debugInfo.frameCount}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DebugAnimationControl;
