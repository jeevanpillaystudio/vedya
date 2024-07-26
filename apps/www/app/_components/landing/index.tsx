"use client";

import { useState } from "react";
import { cn } from "../../_react/css-utils";
import BinaryLoading from "./binary-loading";
import AnimationControl from "./animation-control";

export default function Index() {
  const [debug, setDebug] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(5000); // 5 seconds default
  const [restart, setRestart] = useState(0);

  const handleRestart = () => {
    setRestart((prev) => prev + 1);
    setIsPlaying(true);
  };

  return (
    <main className={cn("h-screen w-screen bg-white")}>
      <BinaryLoading duration={duration} debug={debug} isPlaying={isPlaying} restart={restart} />
      <AnimationControl
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        debug={debug}
        setDebug={setDebug}
        duration={duration}
        setDuration={setDuration}
        onRestart={handleRestart}
      />
    </main>
  );
}
