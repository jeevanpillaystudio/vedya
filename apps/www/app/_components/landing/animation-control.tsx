import React from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

interface AnimationControlProps {
  isPlaying: boolean;
  setIsPlaying: (isPlaying: boolean) => void;
  debug: boolean;
  setDebug: (debug: boolean) => void;
  duration: number;
  setDuration: (duration: number) => void;
  onRestart: () => void;
}

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

const SpeedSlider: React.FC<{ duration: number; setDuration: (duration: number) => void }> = ({ duration, setDuration }) => (
  <div className="flex w-full flex-col space-y-2">
    <label htmlFor="speed" className="text-white">
      Speed: {duration / 1000}s
    </label>
    <Slider id="speed" min={1000} max={10000} step={1000} value={[duration]} onValueChange={(value) => setDuration(value[0]!)} />
  </div>
);

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
    <Card className="fixed right-4 top-4 w-80">
      <CardHeader>
        <CardTitle>Debug Controls</CardTitle>
        <CardDescription className="text-gray-300">Adjust animation settings here.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col space-y-4">
          <div className="flex space-x-2">
            <PlayButton isPlaying={isPlaying} onClick={() => setIsPlaying(!isPlaying)} />
            <RestartButton onClick={onRestart} />
          </div>
          <DebugSwitch debug={debug} setDebug={setDebug} />
          <SpeedSlider duration={duration} setDuration={setDuration} />
        </div>
      </CardContent>
      <CardFooter>
        <p className="text-sm text-gray-400">Animation controls</p>
      </CardFooter>
    </Card>
  );
};

export default AnimationControl;
